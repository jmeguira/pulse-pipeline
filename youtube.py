import json
import os
import random
import re
import string
import subprocess
from datetime import datetime, timedelta, date, timezone
from typing import Tuple

import isodate
import yt_dlp
from dotenv import load_dotenv
from googleapiclient.discovery import build
from moviepy import (
    AudioFileClip,
    VideoFileClip,
    ColorClip,
    concatenate_videoclips,
    afx,
    vfx,
    TextClip,
    CompositeVideoClip,
)
from tqdm import tqdm

"""Load environment variables"""
load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")
ENABLE_LUFS = bool(os.getenv("ENABLE_LUFS", True))
TARGET_LUFS = float(os.getenv("TARGET_LUFS", -14.0))

if not API_KEY:
    raise RuntimeError("Missing YOUTUBE_API_KEY. Set it in .env or your environment.")

ydl_opts_base = {
    "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
    "noplaylist": True,
    "ignoreerrors": True,
    "cookiefile": "cookies.txt",
    "retries": 3,
    "sleep_interval_requests": 0,
    "max_sleep_interval": 5,
    "merge_output_format": "mp4",
    "age_limit": 18,
    "quiet": True,
    "no_warnings": True,
}


# -------------------------
# --- Utilities ----------
# -------------------------
def clean_title(text: str) -> str:
    """Remove hashtags, emojis, and most punctuation for plain-text description."""
    cleaned = re.sub(r"#\S+", "", text)
    cleaned = re.sub(r"[^\x00-\x7F]", "", cleaned)
    allowed = set(string.ascii_letters + string.digits + " .,")
    cleaned = "".join(c if c in allowed else " " for c in cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def keyword_in_title_or_description(
    keyword: str,
    title: str,
    description: str,
) -> bool:
    """
    Returns True if `keyword` or `#keyword` appears as a standalone word
    in either the title or the description.
    """
    keyword = re.escape(keyword.lower())
    text = f"{title} {description}".lower()

    pattern = rf"(?<!\w)(#?{keyword})(?!\w)"
    return re.search(pattern, text) is not None


def transform_clip(clip: VideoFileClip = None) -> VideoFileClip:
    """
    Applies minimally runtime-intensive clip transformations
    """
    speed_factor = 1 + random.uniform(0.025, 0.05)
    tint_factor = 1 + random.uniform(-0.05, 0.1)

    effects = [vfx.MultiplySpeed(factor=speed_factor), vfx.MultiplyColor(factor=tint_factor)]

    try:
        if clip.audio and clip.audio.nchannels == 2:
            pan_factor = random.uniform(-0.1, 0.1)
            effects.append(afx.MultiplyStereoVolume(left=1 - pan_factor, right=1 + pan_factor))
    except Exception:
        pass

    return clip.with_effects(effects)


def normalize_clip_audio(path: str = None):
    tmp = path.replace(".mp4", ".tmp.mp4")

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        path,
        "-af",
        f"loudnorm=I={TARGET_LUFS}:TP=-2:LRA=11",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        tmp,
    ]

    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.replace(tmp, path)


def get_last_week_date_range(target_date: date = None) -> Tuple[date, date]:
    if target_date is None:
        target_date = date.today()

    days_since_sunday = (target_date.weekday() + 1) % 7
    most_recent_sunday = target_date - timedelta(days=days_since_sunday)
    previous_monday = most_recent_sunday - timedelta(days=6)

    return previous_monday, most_recent_sunday


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


# Ordinal helper
def get_ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return str(n) + suffix


def get_compilation_title(
    keyword: str, target_count: int, start_date: date, end_date: date, emoji: str = "😺"
) -> str:
    """
    Generate Youtube compilation title.

    Example output:
    "😺 Top 20 Cat Shorts Weekly Countdown! (Dec 8th–14th, 2025)"
    """
    start_day = get_ordinal(start_date.day)
    end_day = get_ordinal(end_date.day)
    start_month = start_date.strftime("%b")
    end_month = end_date.strftime("%b")
    year = end_date.year

    title = (
        f"{emoji} Top {target_count} {keyword.capitalize()} Shorts Weekly Countdown!"
        + f" ({start_month} {start_day}–{end_month} {end_day}, {year})"
    )
    return title


def get_compilation_description(
    keyword: str,
    target_count: int,
    start_date: date,
    end_date: date,
    videos: list[dict],
) -> str:
    generic_emojis = ["🔥", "⭐", "🎬", "😎", "🎉"]
    emoji = random.choice(generic_emojis)

    start_day = get_ordinal(start_date.day)
    end_day = get_ordinal(end_date.day)
    start_month = start_date.strftime("%b")
    end_month = end_date.strftime("%b")
    year = end_date.year

    first_line = (
        f"{emoji} Weekly roundup: the best {keyword} Shorts from #{target_count}→#1!"
        + f" ({start_month} {start_day}–{end_month} {end_day}, {year})"
    )
    cta_line = f"💬 Comment your favorite clip! #{target_count}→#1"
    subscribe_line = "👍 Don't forget to like and subscribe for more!\n"

    disclaimer = (
        "All clips remain property of their original creators. "
        + "This compilation is edited together for entertainment purposes only. "
        + "Please support the original channels!\n"
    )

    # Video list in markdown
    videos_copy = videos[::-1]  # reversed copy
    video_lines = [f"{idx + 1}. {video['url']}" for idx, video in enumerate(videos_copy)]
    video_list_text = "🔹 Videos included:\n" + "\n".join(video_lines)

    hashtags = (
        f"\n\n#{keyword} #Shorts #YouTubeShorts #Compilation #BestOf"
        + " #Clips #YouTube #Trending #Viral"
    )

    description = "\n".join(
        [first_line, cta_line, subscribe_line, disclaimer, video_list_text, hashtags]
    )

    return description


# -------------------------
# --- YouTube Fetching ----
# -------------------------
def fetch_youtube_shorts(
    keyword: str, target_count=5, batch_size=50, published_after=None, published_before=None
):
    youtube = build("youtube", "v3", developerKey=API_KEY)
    shorts_collected = []
    next_page_token = None
    batch_number = 1

    published_after = datetime.combine(
        published_after,
        datetime.min.time(),
        tzinfo=timezone.utc,
    ).isoformat()

    published_before = datetime.combine(
        published_before + timedelta(days=1),
        datetime.min.time(),
        tzinfo=timezone.utc,
    ).isoformat()

    print(f"🔍 Fetching Shorts for '{keyword}' (target: {target_count})")

    while len(shorts_collected) < target_count:
        print(f"  ➤ Batch #{batch_number}, already collected: {len(shorts_collected)}")

        try:
            search_resp = (
                youtube.search()
                .list(
                    q=keyword,
                    type="video",
                    part="id",
                    maxResults=batch_size,
                    publishedAfter=published_after,
                    publishedBefore=published_before,
                    order="viewCount",
                    pageToken=next_page_token,
                )
                .execute()
            )
        except Exception as e:
            print(f"    ❌ Search failed: {e}")
            break

        video_ids = [item["id"]["videoId"] for item in search_resp.get("items", [])]
        if not video_ids:
            print("    ⚠ No videos found in this batch")
            break

        try:
            videos_resp = (
                youtube.videos()
                .list(part="snippet,contentDetails,statistics", id=",".join(video_ids))
                .execute()
            )
        except Exception as e:
            print(f"    ❌ Failed to fetch video - details: {e}")
            break

        for video in videos_resp.get("items", []):
            duration_sec = int(
                isodate.parse_duration(video["contentDetails"]["duration"]).total_seconds()
            )
            age_restricted = (
                video["contentDetails"].get("contentRating", {}).get("ytRating")
                == "ytAgeRestricted"
            )

            title = video["snippet"].get("title", "").lower()
            description = video["snippet"].get("description", "").lower()
            keyword_match = keyword_in_title_or_description(keyword, title, description)

            if duration_sec <= 60 and not age_restricted and keyword_match:
                shorts_collected.append(
                    {
                        "id": video["id"],
                        "title": video["snippet"]["title"],
                        "uploader": video["snippet"]["channelTitle"],
                        "channel_id": video["snippet"]["channelId"],
                        "url": f"https://www.youtube.com/watch?v={video['id']}",
                        "upload_date": video["snippet"]["publishedAt"],
                        "view_count": int(video["statistics"].get("viewCount", 0)),
                        "duration": duration_sec,
                    }
                )

        next_page_token = search_resp.get("nextPageToken")
        if not next_page_token:
            break

        batch_number += 1

    shorts_collected.sort(key=lambda x: x["view_count"], reverse=True)
    return shorts_collected[:target_count]


def download_youtube_shorts(folder: str = None, keyword: str = None, shorts=None):
    ydl_opts = {**ydl_opts_base, "outtmpl": os.path.join(folder, "%(id)s.%(ext)s")}

    metadata = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for short in tqdm(shorts, desc=f"Downloading {len(shorts)} shorts for '{keyword}'"):
            try:
                ydl.download([short["url"]])
            except Exception as e:
                print(f"❌ Failed to download {short['url']}: {e}")
                continue

            metadata_entry = {
                "title": clean_title(short["title"]),
                "uploader": short["uploader"],
                "url": short["url"],
                "upload_date": short["upload_date"],
                "view_count": short["view_count"],
                "duration": short["duration"],
                "file_path": os.path.join(folder, f"{short['id']}.mp4"),
                "channel_id": short["channel_id"],
                "channel_url": f"https://www.youtube.com/channel/{short['channel_id']}",
            }
            metadata.append(metadata_entry)

    if metadata:
        metadata_file = os.path.join(folder, "metadata.json")
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)

        print(
            f"✅ Finished downloading {len(shorts)} shorts for keyword: '{keyword}' \nShorts saved in {folder}"
        )


# -------------------------
# --- Video Compilation ---
# -------------------------
def create_compilation(
    keyword: str = None,
    folder: str = None,
    title_card_path: str = "title_card.mp4",
    transition_sound_path: str = "pop.wav",
    output_width: int = 1920,
    output_height: int = 1080,
):
    """
    Creates a horizontal (16:9) compilation video:
      - Title card at the start
      - Subtle random color/tint per clip
      - Faint watermark overlay
      - Vertical videos: blurred background approximation
      - Random transition sounds with fade-out between clips
    """
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
        normalize_clip_audio(title_card_path)
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
            if ENABLE_LUFS:
                try:
                    normalize_clip_audio(video["file_path"])
                except Exception as e:
                    print(f"⚠ Failed to normalize {video['file_path']}: {e}")

            clip = VideoFileClip(video["file_path"]).resized(height=output_height)
            clip = transform_clip(clip)

            clips.append(clip)

        except Exception as e:
            print(f"⚠ Failed to pre-process {video['file_path']}: {e}")
    clips.append(get_outro_clip())
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
        keyword=keyword,
        target_count=len(videos),
        start_date=published_after,
        end_date=published_before,
    )

    description = get_compilation_description(
        keyword=keyword,
        target_count=len(videos),
        start_date=published_after,
        end_date=published_before,
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
def build_compilation(
    keyword: str = None,
    target_count: int = 5,
    published_after: date = None,
    published_before: date = None,
    base_output_path: str = "downloads/",
):
    date_range_str = (
        published_after.strftime("%Y-%m-%d") + "_" + published_before.strftime("%Y-%m-%d")
    )

    print(
        f"\n🔍 Creating compilation video for keyword: '{keyword}' | target_count: '{target_count}'"
    )
    folder = os.path.join(base_output_path, keyword, date_range_str)
    os.makedirs(folder, exist_ok=True)

    print(f"⬇ Fetching new Shorts for '{keyword}'...")
    shorts = fetch_youtube_shorts(
        keyword=keyword,
        target_count=target_count,
        published_after=published_after,
        published_before=published_before,
    )

    if not shorts:
        print(f"No Shorts found for '{keyword}'")
        return

    download_youtube_shorts(folder=folder, keyword=keyword, shorts=shorts)

    # --- Create compilation ---
    try:
        create_compilation(
            keyword=keyword,
            folder=folder,
        )
    except Exception as e:
        print(f"⚠ Failed to create compilation for '{keyword}': {e}")
        return


# -------------------------
# --- Run Script ----------
# -------------------------
if __name__ == "__main__":
    keywords = ["fart"]
    target_count = 3
    published_after, published_before = get_last_week_date_range()
    for keyword in keywords:
        build_compilation(
            keyword=keyword,
            target_count=target_count,
            published_after=published_after,
            published_before=published_before,
        )
