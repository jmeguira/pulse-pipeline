import json
import os

from moviepy import (
    CompositeVideoClip,
    ColorClip,
    TextClip,
    AudioFileClip,
    VideoFileClip,
    concatenate_videoclips,
)
from tqdm import tqdm

from config.run_config import RunConfig
from utils.metadata_utils import get_compilation_title, get_compilation_description
from utils.transform_utils import normalize_clip_audio, transform_clip


def get_outro_clip(output_width=1920, output_height=1080, duration=3.0) -> CompositeVideoClip:
    bg = ColorClip(size=(output_width, output_height), color=(0, 0, 0), duration=duration)

    top_text = TextClip(
        text="THANKS FOR WATCHING!",
        font_size=int(output_height * 0.15),
        size=(output_width, output_height),
        color="white",
        font="Impact",
        vertical_align="top",
        duration=duration,
    )

    bottom_text = TextClip(
        text="SUBSCRIBE FOR MORE",
        font_size=int(output_height * 0.15),
        size=(output_width, output_height),
        color="white",
        font="Impact",
        duration=duration,
    )

    return CompositeVideoClip([bg, top_text, bottom_text])


# -------------------------
# --- Video Compilation ---
# -------------------------
def create_compilation(
    run_config: RunConfig,
    folder: str = None,
    title_card_path: str = "title_card.mp4",
    transition_sound_path: str = "pop.wav",
    output_width: int = 1920,
    output_height: int = 1080,
    vfx=None,
):
    """
    Creates a horizontal (16:9) compilation video:
      - Title card at the start
      - Subtle random color/tint per clip
      - Faint watermark overlay
      - Vertical videos: blurred background approximation
      - Random transition sounds with fade-out between clips
    """
    keyword = run_config.keyword
    metadata_path = os.path.join(folder, "metadata.json")
    output_path = os.path.join(folder, f"{keyword}_compilation.mp4")
    transition_duration = 1

    if not os.path.exists(metadata_path):
        print(f"⚠ No metadata.json found for '{keyword}', skipping compilation.")
        return

    with open(metadata_path, "r", encoding="utf-8") as f:
        videos = json.load(f)

    if not videos:
        print(f"⚠ No videos found in metadata for '{keyword}'.")
        return

    # Sort videos by view count ascending
    videos.sort(key=lambda v: v["view_count"])

    if os.path.exists(transition_sound_path):
        transition_sound_clip = AudioFileClip(transition_sound_path).subclipped(
            0, transition_duration
        )

        transition_clip = ColorClip(
            size=(1920, 1080), color=(0, 0, 0), duration=transition_duration
        )
        transition_clip = transition_clip.with_audio(transition_sound_clip)
    else:
        print(f"⚠ No transition audio found at  at {transition_sound_path}")
        return

    clips = []
    # --- Title Card ---
    if os.path.exists(title_card_path):
        title_clip = VideoFileClip(title_card_path)
        title_clip = title_clip.with_effects([vfx.Resize((output_width, output_height))])
        clips.append(title_clip)
    else:
        print(f"⚠ No title card found at {title_card_path}")
        return

    num_clips = len(videos)
    for idx, video in enumerate(tqdm(videos, "Pre-processing clips")):
        try:
            index = num_clips - idx
            # centered bold text
            text_clip = TextClip(
                text="#" + str(index),
                font_size=int(output_height * 0.28),  # scales automatically
                size=(output_width, output_height),
                color="#4C7EFF",
                font="Impact",
                horizontal_align="center",
                vertical_align="center",
                duration=transition_duration,
            )

            # combine layers
            tmp_clip = CompositeVideoClip([transition_clip, text_clip])

            clips.append(tmp_clip)
            if run_config.enable_lufs:
                try:
                    normalize_clip_audio(run_config, video["file_path"])
                except Exception as e:
                    print(f"⚠ Failed to normalize {video['file_path']}: {e}")

            clip = VideoFileClip(video["file_path"]).resized(height=output_height)
            clip = transform_clip(clip)

            clips.append(clip)

        except Exception as e:
            print(f"⚠ Failed to pre-process {video['file_path']}: {e}")
    clips.append(get_outro_clip())

    title_clip = VideoFileClip(title_card_path)
    title_clip = title_clip.with_effects([vfx.Resize((output_width, output_height))])
    clips.append(title_clip)

    # --- Concatenate all clips ---
    final = concatenate_videoclips(
        clips,
        method="compose",
    )
    final.write_videofile(
        output_path,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        bitrate="8000k",
        threads=4,
    )

    print(f"✅ Compilation created: {output_path}")

    # --- Generate title & description ---
    title = get_compilation_title(
        run_config=run_config,
    )

    description = get_compilation_description(
        run_config=run_config,
        videos=videos,
    )

    # Write to files in the same folder as the compilation video
    with open(os.path.join(folder, "title.txt"), "w", encoding="utf-8") as f:
        f.write(title)

    with open(os.path.join(folder, "description.txt"), "w", encoding="utf-8") as f:
        f.write(description)

    print(f"✅ Title & description saved in: {folder}")


# -------------------------
# --- Main Download & Compile ---
# -------------------------
def fetch_youtube_shorts(run_config):
    pass


def download_youtube_shorts(run_config, folder, shorts):
    pass


def build_compilation(
    run_config: RunConfig,
    base_output_path: str = "downloads/",
):
    keyword = run_config.keyword
    target_count = run_config.target_count
    published_after = run_config.published_after
    published_before = run_config.published_before
    date_range_str = (
        published_after.strftime("%Y-%m-%d") + "_" + published_before.strftime("%Y-%m-%d")
    )

    print(
        f"\n🔍 Creating compilation video for keyword: '{keyword}' | target_count: '{target_count}'"
    )
    folder = os.path.join(base_output_path, keyword, date_range_str)
    os.makedirs(folder, exist_ok=True)

    print(f"⬇ Fetching new Shorts for '{keyword}'...")
    shorts = fetch_youtube_shorts(run_config)

    if not shorts:
        print(f"No Shorts found for '{keyword}'")
        return

    download_youtube_shorts(run_config=run_config, folder=folder, shorts=shorts)

    # --- Create compilation ---
    try:
        create_compilation(
            run_config=run_config,
            folder=folder,
        )
    except Exception as e:
        print(f"⚠ Failed to create compilation for '{keyword}': {e}")
        return
