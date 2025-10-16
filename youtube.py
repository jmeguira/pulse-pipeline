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

"""Load environment variables"""
load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")

if not API_KEY:
    raise RuntimeError("Missing YOUTUBE_API_KEY. Set it in .env or your environment.")


def clean_title(text: str) -> str:
    """
    Remove hashtags, emojis, and most punctuation for a clean plain-text description.
    Keeps only letters, numbers, spaces, and basic punctuation (.,-)
    """
    # 1. Remove hashtags
    cleaned = re.sub(r"#\S+", "", text)

    # 2. Remove emojis and non-ASCII symbols
    cleaned = re.sub(r"[^\x00-\x7F]", "", cleaned)

    # 3. Remove most punctuation except basic sentence punctuation
    allowed = set(string.ascii_letters + string.digits + " .,")
    cleaned = "".join(c if c in allowed else " " for c in cleaned)

    # 4. Collapse multiple spaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned


def fetch_youtube_shorts(keyword: str, target_count=5, days_back=2, batch_size=50):
    """
    Fetch YouTube Shorts metadata under 60s, not age-restricted, sorted by view count.
    Returns a list of dictionaries containing video info.
    """
    youtube = build("youtube", "v3", developerKey=API_KEY)
    cutoff_date = (datetime.utcnow() - timedelta(days=days_back)).isoformat("T") + "Z"

    shorts_collected = []
    next_page_token = None
    batch_number = 1

    print(f"🔍 Fetching Shorts for '{keyword}' (target: {target_count})")

    while len(shorts_collected) < target_count:
        print(f"  ➤ Batch #{batch_number}, already collected: {len(shorts_collected)}")

        # --- Fetch video IDs ---
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

        # --- Fetch full video details ---
        try:
            videos_resp = (
                youtube.videos()
                .list(part="snippet,contentDetails,statistics", id=",".join(video_ids))
                .execute()
            )
        except Exception as e:
            print(f"    ❌ Failed to fetch video details: {e}")
            break

        # --- Filter valid Shorts ---
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

        print(f"    ➤ Batch #{batch_number} added {len(shorts_collected)} valid Shorts")

        # --- Prepare for next batch ---
        next_page_token = search_resp.get("nextPageToken")
        if not next_page_token:
            print(f"    ⚠ No more pages available")
            break

        batch_number += 1

    # Sort by view count and return only target_count
    shorts_collected.sort(key=lambda x: x["view_count"], reverse=True)
    return shorts_collected[:target_count]


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
        # Suppress all normal output; errors will still be shown
        "quiet": True,
        "no_warnings": True,
    }

    for keyword in keywords:
        print(f"\n🔍 Searching for keyword: '{keyword}'")
        keyword_folder = os.path.join(base_output_path, keyword, today_str)
        os.makedirs(keyword_folder, exist_ok=True)

        # Fetch metadata
        shorts = fetch_youtube_shorts(keyword, target_count_per_keyword, days_back)
        if not shorts:
            print(f"No Shorts found for '{keyword}'")
            continue

        all_description_lines = []
        centralized_metadata = []

        # Use one YoutubeDL instance per batch, specifying the folder template
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

        # Save description & metadata if any videos were downloaded
        if centralized_metadata:
            desc_file = os.path.join(keyword_folder, "description.txt")
            metadata_file = os.path.join(keyword_folder, "metadata.json")

            with open(desc_file, "w", encoding="utf-8") as f:
                f.write("\n".join(all_description_lines))

            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(centralized_metadata, f, indent=4)

            print(f"✅ Finished '{keyword}' — {len(shorts)} Shorts saved in {keyword_folder}")


if __name__ == "__main__":
    keywords = ["cat", "fail"]
    target_count_per_keyword = 5
    search_and_download_shorts(keywords, target_count_per_keyword)
