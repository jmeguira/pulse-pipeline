import os
import json
from datetime import datetime, timedelta
import re
from tqdm import tqdm
from googleapiclient.discovery import build
import isodate
import yt_dlp

API_KEY = "AIzaSyDo7rQboCzNGx8OlEuHkcickWZ7sgkxUnA"

def clean_title(text: str) -> str:
    """Remove hashtags and extra whitespace from a title."""
    no_tags = re.sub(r"#\S+", "", text)
    cleaned = re.sub(r"\s+", " ", no_tags).strip()
    return cleaned

def fetch_youtube_shorts(keyword: str, max_results=50, days_back=2):
    """
    Fetch metadata for YouTube Shorts under 60s, not age-restricted, sorted by view count.
    """
    youtube = build("youtube", "v3", developerKey=API_KEY)
    cutoff_date = (datetime.utcnow() - timedelta(days=days_back)).isoformat("T") + "Z"

    # 1️⃣ Search for videos by keyword, sorted by view count
    search_response = youtube.search().list(
        q=keyword,
        type="video",
        part="id",
        maxResults=max_results,
        publishedAfter=cutoff_date,
        order="viewCount"
    ).execute()

    video_ids = [item["id"]["videoId"] for item in search_response.get("items", [])]
    if not video_ids:
        return []

    # 2️⃣ Fetch video details (duration, uploader, stats)
    videos_response = youtube.videos().list(
        part="snippet,contentDetails,statistics",
        id=",".join(video_ids)
    ).execute()

    shorts = []
    for video in videos_response.get("items", []):
        duration_sec = int(isodate.parse_duration(video["contentDetails"]["duration"]).total_seconds())
        age_restricted = video["contentDetails"].get("contentRating", {}).get("ytRating") == "ytAgeRestricted"

        if duration_sec <= 60 and not age_restricted:
            shorts.append({
                "id": video["id"],
                "title": video["snippet"]["title"],
                "uploader": video["snippet"]["channelTitle"],
                "url": f"https://www.youtube.com/watch?v={video['id']}",
                "upload_date": video["snippet"]["publishedAt"],
                "view_count": int(video["statistics"].get("viewCount", 0)),
                "duration": duration_sec
            })

    return shorts

def search_and_download_shorts(keywords, target_count_per_keyword=5, base_output_path="downloads/", days_back=2):
    today_str = datetime.today().strftime("%Y-%m-%d")

    ydl_opts_base = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "noplaylist": True,
        "quiet": False,
        "ignoreerrors": True,
        "cookiefile": "cookies.txt",
        "download_archive": "downloaded.txt",  # persistent deduplication
        "retries": 3,
        "sleep_interval_requests": 0,
        "max_sleep_interval": 5,
        "merge_output_format": "mp4",
        "age_limit": 18,
    }

    with yt_dlp.YoutubeDL(ydl_opts_base) as ydl:
        for keyword in keywords:
            print(f"\n🔍 Searching for keyword: '{keyword}'")
            keyword_folder = os.path.join(base_output_path, keyword_safe, today_str)
            os.makedirs(keyword_folder, exist_ok=True)

            # Fetch metadata from YouTube Data API
            shorts = fetch_youtube_shorts(keyword, max_results=target_count_per_keyword * 3, days_back=days_back)
            if not shorts:
                print(f"No Shorts found for '{keyword}'")
                continue

            # Sort by view count descending, then slice to target
            shorts_sorted = sorted(shorts, key=lambda x: x["view_count"], reverse=True)[:target_count_per_keyword]

            all_description_lines = []
            centralized_metadata = []

            # Download loop with progress bar
            for entry in tqdm(shorts_sorted, desc=f"Downloading Shorts for '{keyword}'"):
                url = entry["url"]
                video_id = entry["id"]
                outtmpl = os.path.join(keyword_folder, f"{video_id}.%(ext)s")

                try:
                    with yt_dlp.YoutubeDL({
                        **ydl_opts_base,
                        "outtmpl": outtmpl,
                        "quiet": True,
                        "no_warnings": True
                    }) as ydl_single:
                        ydl_single.download([url])

                    metadata_entry = {
                        "title": clean_title(entry["title"]),
                        "uploader": entry["uploader"],
                        "url": url,
                        "upload_date": entry["upload_date"],
                        "view_count": entry["view_count"],
                        "duration": entry["duration"],
                        "keywords": keyword,
                        "file_path": outtmpl
                    }
                    centralized_metadata.append(metadata_entry)
                    all_description_lines.append(
                        f"{clean_title(metadata_entry['title'])} - by {metadata_entry['uploader']} ({metadata_entry['url']})"
                    )

                except Exception as e:
                    print(f"Failed to download {url}: {e}")

            print(f"✅ Finished downloading {len(shorts_sorted)} Shorts for '{keyword}' on {today_str}")

            # --- Save metadata/description per keyword ---
            if centralized_metadata:
                desc_file = os.path.join(keyword_folder, "description.txt")
                with open(desc_file, "w", encoding="utf-8") as f:
                    f.write("\n".join(all_description_lines))
                print(f"✅ Description file created for '{keyword}': {desc_file}")

                metadata_file = os.path.join(keyword_folder, "metadata.json")
                with open(metadata_file, "w", encoding="utf-8") as f:
                    json.dump(centralized_metadata, f, indent=4)
                print(f"✅ Metadata JSON created for '{keyword}': {metadata_file}")


if __name__ == "__main__":
    keywords = ["cat", "fail"]
    target_count_per_keyword = 3
    search_and_download_shorts(keywords, target_count_per_keyword)
