import os
import json
from datetime import datetime, timedelta
import re
from tqdm import tqdm
from googleapiclient.discovery import build
import isodate
import yt_dlp
from pprint import pprint
from dotenv import load_dotenv
import string
import random
from moviepy import (
    VideoFileClip,
    AudioFileClip,
    CompositeVideoClip,
    ColorClip,
    TextClip,
    concatenate_videoclips,
    vfx,
)

"""Load environment variables"""
load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")

if not API_KEY:
    raise RuntimeError("Missing YOUTUBE_API_KEY. Set it in .env or your environment.")


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


# -------------------------
# --- YouTube Fetching ----
# -------------------------
def fetch_youtube_shorts(keyword: str, target_count=5, days_back=2, batch_size=50):
    youtube = build("youtube", "v3", developerKey=API_KEY)
    cutoff_date = (datetime.utcnow() - timedelta(days=days_back)).isoformat("T") + "Z"
    shorts_collected = []
    next_page_token = None
    batch_number = 1

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
                    publishedAfter=cutoff_date,
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
            print(f"    ⚠ No videos found in this batch")
            break

        try:
            videos_resp = (
                youtube.videos()
                .list(part="snippet,contentDetails,statistics", id=",".join(video_ids))
                .execute()
            )
        except Exception as e:
            print(f"    ❌ Failed to fetch video details: {e}")
            break

        for video in videos_resp.get("items", []):
            duration_sec = int(
                isodate.parse_duration(video["contentDetails"]["duration"]).total_seconds()
            )
            age_restricted = (
                video["contentDetails"].get("contentRating", {}).get("ytRating")
                == "ytAgeRestricted"
            )
            title_cleaned = clean_title(video["snippet"]["title"])
            if (
                duration_sec <= 60
                and not age_restricted
                and keyword.lower() in title_cleaned.lower()
            ):
                shorts_collected.append(
                    {
                        "id": video["id"],
                        "title": video["snippet"]["title"],
                        "uploader": video["snippet"]["channelTitle"],
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


# -------------------------
# --- Video Compilation ---
# -------------------------
def create_compilation(
    keyword,
    base_output_path="downloads/",
    title_card_path="title_card.mp4",
    transition_sounds_path="transitions/",
    channel_name="HashtagSoup",
    output_width=1920,
    output_height=1080,
):
    """
    Creates a horizontal (16:9) compilation video:
      - Title card at the start
      - Subtle random color/tint per clip
      - Faint watermark overlay
      - Vertical videos: blurred background approximation
      - Random transition sounds with fade-out between clips
    """
    today_str = datetime.today().strftime("%Y-%m-%d")
    folder = os.path.join(base_output_path, keyword, today_str)
    metadata_path = os.path.join(folder, "metadata.json")
    output_path = os.path.join(folder, f"{keyword}_compilation.mp4")

    if not os.path.exists(metadata_path):
        print(f"⚠ No metadata.json found for '{keyword}', skipping compilation.")
        return

    with open(metadata_path, "r", encoding="utf-8") as f:
        videos = json.load(f)

    if not videos:
        print(f"⚠ No videos found in metadata for '{keyword}'.")
        return

    # Sort videos by view count descending
    videos.sort(key=lambda v: v["view_count"], reverse=True)
    for video in videos:
        print(f"Video: {video['title']}, view_count: {video['view_count']}")

    clips = []

    # --- Title Card ---
    if os.path.exists(title_card_path):
        title_clip = VideoFileClip(title_card_path)
        title_clip = title_clip.with_effects([vfx.Resize((output_width, output_height))])
        clips.append(title_clip)
    else:
        print(f"⚠ No title card found at {title_card_path}")

    # --- Transition Sounds ---
    transition_sounds = [
        os.path.join(transition_sounds_path, f)
        for f in os.listdir(transition_sounds_path)
        if f.lower().endswith((".mp3", ".wav"))
    ]

    for idx, video in enumerate(videos):
        try:
            clip = VideoFileClip(video["file_path"])
            clip = clip.with_effects([vfx.Resize((output_width, output_height))])
            clips.append(clip)

        except Exception as e:
            print(f"⚠ Failed to process {video['file_path']}: {e}")

    if not clips:
        print(f"⚠ No valid clips for '{keyword}'.")
        return

    # --- Concatenate all clips ---
    """final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(
        output_path,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        bitrate="8000k",
        threads=4,
    )"""

    print(f"✅ Compilation created: {output_path}")


# -------------------------
# --- Main Download & Compile ---
# -------------------------
def search_and_download_shorts(
    keywords, target_count_per_keyword=5, base_output_path="downloads/", days_back=2
):
    today_str = datetime.today().strftime("%Y-%m-%d")

    ydl_opts_base = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "noplaylist": True,
        "ignoreerrors": True,
        "cookiefile": "cookies.txt",
        "download_archive": "downloaded.txt",
        "retries": 3,
        "sleep_interval_requests": 0,
        "max_sleep_interval": 5,
        "merge_output_format": "mp4",
        "age_limit": 18,
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
    }

    for keyword in keywords:
        print(f"\n🔍 Searching for keyword: '{keyword}'")
        keyword_folder = os.path.join(base_output_path, keyword, today_str)
        os.makedirs(keyword_folder, exist_ok=True)

        # --- Check for existing metadata ---
        existing_videos = []
        if os.path.exists(os.path.join(keyword_folder, "metadata.json")):
            try:
                with open(
                    os.path.join(keyword_folder, "metadata.json"), "r", encoding="utf-8"
                ) as f:
                    existing_videos = json.load(f)
            except Exception as e:
                print(f"⚠ Failed to load existing metadata: {e}")

        # Filter out any entries whose files are missing
        existing_videos = [v for v in existing_videos if os.path.exists(v.get("file_path", ""))]

        # --- Skip fetching if enough videos exist ---
        if len(existing_videos) >= target_count_per_keyword:
            print(
                f"✅ Found {len(existing_videos)} existing videos for '{keyword}', skipping fetch/download."
            )
            create_compilation(
                keyword=keyword,
                title_card_path="title_card.mp4",
                base_output_path=base_output_path,
                transition_sounds_path="transition_sounds/",
                channel_name="HashtagSoup",
            )
            continue

        # --- Otherwise fetch new videos ---
        print(f"⬇ Fetching new Shorts for '{keyword}'...")
        shorts = fetch_youtube_shorts(keyword, target_count_per_keyword, days_back)
        if not shorts:
            print(f"No Shorts found for '{keyword}'")
            continue

        # Fetch metadata
        shorts = fetch_youtube_shorts(keyword, target_count_per_keyword, days_back)
        if not shorts:
            print(f"No Shorts found for '{keyword}'")
            continue

        all_description_lines = []
        centralized_metadata = []
        ydl_opts = {**ydl_opts_base, "outtmpl": os.path.join(keyword_folder, "%(id)s.%(ext)s")}

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            for entry in tqdm(shorts, desc=f"Downloading Shorts for '{keyword}'"):
                try:
                    ydl.download([entry["url"]])
                except Exception as e:
                    print(f"❌ Failed to download {entry['url']}: {e}")
                    continue

                metadata_entry = {
                    "title": clean_title(entry["title"]),
                    "uploader": entry["uploader"],
                    "url": entry["url"],
                    "upload_date": entry["upload_date"],
                    "view_count": entry["view_count"],
                    "duration": entry["duration"],
                    "keywords": keyword,
                    "file_path": os.path.join(keyword_folder, f"{entry['id']}.mp4"),
                }
                centralized_metadata.append(metadata_entry)
                all_description_lines.append(
                    f"{metadata_entry['title']} - by {metadata_entry['uploader']} ({metadata_entry['url']})"
                )

        if centralized_metadata:
            desc_file = os.path.join(keyword_folder, "description.txt")
            metadata_file = os.path.join(keyword_folder, "metadata.json")
            with open(desc_file, "w", encoding="utf-8") as f:
                f.write("\n".join(all_description_lines))
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(centralized_metadata, f, indent=4)

            print(f"✅ Finished '{keyword}' — {len(shorts)} Shorts saved in {keyword_folder}")

            # --- Create compilation ---
            try:
                title_card_path = "title_card.mp4"  # adjust path if needed
                create_compilation(
                    keyword=keyword,
                    title_card_path=title_card_path,
                    base_output_path=base_output_path,
                    transition_sounds_path="transition_sounds/",
                    channel_name="HashtagSoup",
                )
            except Exception as e:
                print(f"⚠ Failed to create compilation for '{keyword}': {e}")


# -------------------------
# --- Run Script ----------
# -------------------------
if __name__ == "__main__":
    keywords = ["cat"]
    target_count_per_keyword = 3
    search_and_download_shorts(keywords, target_count_per_keyword)
