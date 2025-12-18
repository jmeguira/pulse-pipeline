import json
import os

from moviepy import (
    AudioFileClip,
    ColorClip,
    VideoFileClip,
    vfx,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips,
)
from tqdm import tqdm

from types.stage import Stage
from utils.compile_utils import get_outro_clip


class CompileStage(Stage):
    @property
    def name(self):
        return "Compile Video"

    def should_run(self):
        # e.g., skip if compilation already exists
        return True

    def run(self):
        keyword = self.context.run_config.keyword
        metadata_path = os.path.join(self.context.run_config.OUTPUT_FULL_PATH, "metadata.json")
        output_path = os.path.join(
            self.context.run_config.OUTPUT_FULL_PATH, f"{keyword}_compilation.mp4"
        )
        transition_sound_path = self.context.run_config.TRANSITION_SOUND_PATH
        title_card_path = self.context.run_config.TITLE_CARD_PATH
        output_width = self.context.run_config.OUTPUT_WIDTH
        output_height = self.context.run_config.OUTPUT_HEIGHT
        transition_duration = self.context.run_config.TRANSITION_DURATION
        target_fps = self.context.run_config.TARGET_FPS

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
                size=(output_width, output_height), color=(0, 0, 0), duration=transition_duration
            )
            transition_clip = transition_clip.with_audio(transition_sound_clip)
        else:
            print(
                f"⚠ No transition audio found at  at {self.context.run_config.TRANSITION_SOUND_PATH}"
            )
            return

        output_clips = []
        # --- Title Card ---
        if os.path.exists(title_card_path):
            title_clip = VideoFileClip(title_card_path)
            title_clip = title_clip.with_effects([vfx.Resize((output_width, output_height))])
            output_clips.append(title_clip)
        else:
            print(f"⚠ No title card found at {title_card_path}")
            return

        num_clips = len(videos)
        for idx, clip in enumerate(tqdm(self.context.clips, "Compiling clips")):
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

                output_clips.append(tmp_clip)
                output_clips.append(clip)

            except Exception as e:
                print(f"⚠ Failed to pre-process {clip['file_path']}: {e}")

        output_clips.append(get_outro_clip())

        title_clip = VideoFileClip(title_card_path)
        title_clip = title_clip.with_effects([vfx.Resize((output_width, output_height))])
        output_clips.append(title_clip)

        # --- Concatenate all clips ---
        final = concatenate_videoclips(
            output_clips,
            method="compose",
        )
        final.write_videofile(
            output_path,
            fps=target_fps,
            codec="libx264",
            audio_codec="aac",
            bitrate="8000k",
            threads=4,
        )

        for clip in output_clips:
            clip.close()
        final.close()
