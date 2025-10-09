import yt_dlp
import os
import json
from datetime import datetime, timedelta
import re

def sanitize_filename(name):
    """Remove problematic characters from filenames."""
    return re.sub(r'[\\/*?:"<>|]', "_", name)

def search_and_download_shorts(
    keywords,
    target_count_per_keyword=5,
    base_output_path="downloads/",
    days_back=2
):
    cutoff_date = datetime.today() - timedelta(days=days_back)
    cutoff_date_str = cutoff_date.strftime("%Y%m%d")
    today_str = datetime.today().strftime("%Y-%m-%d")

    all_description_lines = []
    centralized_metadata = []

    # Base options
    ydl_opts_base = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "noplaylist": True,
        "quiet": False,
        "ignoreerrors": True,
        "cookiefile": "cookies.txt",
        "download_archive": "downloaded.txt",
        "retries": 3,
        "sleep_interval_requests": 0,
        "max_sleep_interval": 5,
        "merge_output_format": "mp4",
        "dateafter": cutoff_date_str,
    }

    with yt_dlp.YoutubeDL(ydl_opts_base) as ydl:
        for keyword in keywords:
            print(f"\n🔍 Searching for keyword: '{keyword}'")
            keyword_safe = sanitize_filename(keyword)
            keyword_folder = os.path.join(base_output_path, keyword_safe, today_str)
            os.makedirs(keyword_folder, exist_ok=True)

            downloaded = 0

            # Search for more results than needed to filter Shorts
            search_query = f"ytsearch{target_count_per_keyword*5}:{keyword}"
            try:
                results = ydl.extract_info(search_query, download=False)
            except Exception as e:
                print(f"Search failed for '{keyword}': {e}")
                continue

            # Filter Shorts <=60s
            shorts_filtered = [
                v for v in results.get("entries", [])
                if v and v.get("duration") is not None and v.get("duration") <= 60
            ]

            # Sort by view count descending and keep only top N
            shorts_sorted = sorted(shorts_filtered, key=lambda x: x.get("view_count", 0), reverse=True)[:target_count_per_keyword]


            for entry in shorts_sorted[:target_count_per_keyword]:
                url = entry["webpage_url"]
                outtmpl = os.path.join(keyword_folder, f"{title_safe} [{entry.get('id')}.%(ext)s")

                try:
                    print(f"Downloading Short: {entry.get('title')}")
                    # Fresh YoutubeDL per video
                    with yt_dlp.YoutubeDL({**ydl_opts_base, "outtmpl": outtmpl}) as ydl_single:
                        ydl_single.download([url])

                    # Metadata
                    metadata_entry = {
                        "title": entry.get("title", "Untitled"),
                        "uploader": entry.get("uploader", "Unknown"),
                        "url": url,
                        "upload_date": entry.get("upload_date"),
                        "view_count": entry.get("view_count"),
                        "duration": entry.get("duration"),
                        "keywords": keyword,
                        "file_path": outtmpl
                    }
                    centralized_metadata.append(metadata_entry)
                    all_description_lines.append(
                        f"{metadata_entry['title']} - by {metadata_entry['uploader']} ({metadata_entry['url']})"
                    )
                except Exception as e:
                    print(f"Failed to download {url}: {e}")

                downloaded += 1

            print(f"✅ Finished downloading {downloaded} Shorts for '{keyword}' on {today_str}")

    # Save centralized description and metadata
    if centralized_metadata:
        description_folder = os.path.join(base_output_path, today_str)
        os.makedirs(description_folder, exist_ok=True)

        desc_file = os.path.join(description_folder, "description.txt")
        with open(desc_file, "w", encoding="utf-8") as f:
            f.write("\n".join(all_description_lines))
        print(f"✅ Combined description file created: {desc_file}")

        metadata_file = os.path.join(description_folder, "metadata.json")
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(centralized_metadata, f, indent=4)
        print(f"✅ Centralized metadata JSON created: {metadata_file}")


if __name__ == "__main__":
    keywords = ["cat"]
    target_count_per_keyword = 15
    search_and_download_shorts(keywords, target_count_per_keyword)
