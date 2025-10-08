import yt_dlp
import os
import json
from datetime import datetime, timedelta
import re
from urllib.parse import quote

def sanitize_filename(name):
    """Remove problematic characters from filenames."""
    return re.sub(r'[\\/*?:"<>|]', "_", name)

def build_youtube_search_url(keyword: str, sort_by: str = "view_count", page_token: str = None) -> str:
    """
    Build a YouTube search URL with sorting and pagination.
    """
    # Map sort_by to YouTube sp codes
    sort_map = {
        "relevance": "CAASAhAB",
        "view_count": "CAM%3D",
        "upload_date": "EgQIARAB",
        "rating": "CAE%3D"
    }

    if sort_by not in sort_map:
        raise ValueError(f"Invalid sort_by value: {sort_by}")

    sp_value = sort_map[sort_by]
    keyword_encoded = quote(keyword)
    url = f"https://www.youtube.com/results?search_query={keyword_encoded}&sp={sp_value}"

    if page_token:
        url += f"&page_token={page_token}"

    return url

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

    ydl_opts = {
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
        "writeinfojson": True,
        "dateafter": cutoff_date_str,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for keyword in keywords:
            print(f"\n🔍 Searching for keyword: '{keyword}'")
            keyword_safe = sanitize_filename(keyword)
            keyword_folder = os.path.join(base_output_path, keyword_safe, today_str)
            os.makedirs(keyword_folder, exist_ok=True)

            downloaded = 0
            shorts_urls = set()
            next_page_token = None

            while downloaded < target_count_per_keyword:
                search_url = build_youtube_search_url(keyword, sort_by="view_count", page_token=next_page_token)
                print(f"Searching for '{keyword}' using URL: {search_url}")

                try:
                    results = ydl.extract_info(search_url, download=False)
                except Exception as e:
                    print(f"Search failed for '{keyword}': {e}")
                    break

                shorts_filtered = [
                    v for v in results.get("entries", [])
                    if v
                    and v.get("duration") is not None
                    and v.get("duration") <= 60
                    and v.get("webpage_url") not in shorts_urls
                ]

                if not shorts_filtered:
                    print("No more Shorts found in this page.")
                    break

                # Sort by view count descending
                shorts_sorted = sorted(shorts_filtered, key=lambda x: x.get("view_count", 0), reverse=True)

                for entry in shorts_sorted:
                    if downloaded >= target_count_per_keyword:
                        break

                    url = entry["webpage_url"]
                    title_safe = sanitize_filename(entry.get("title", "Untitled"))
                    outtmpl = os.path.join(keyword_folder, f"{title_safe} [{entry.get('id')}].%(ext)s")
                    ydl.params["outtmpl"] = outtmpl

                    try:
                        print(f"Downloading Short: {entry.get('title')}")
                        ydl.download([url])
                        shorts_urls.add(url)
                        downloaded += 1

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

                # Get next page token for pagination
                next_page_token = results.get("next_page_token")
                if not next_page_token:
                    break  # no more pages

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
    keywords = ["funny cats", "fails"]
    target_count_per_keyword = 3
    search_and_download_shorts(keywords, target_count_per_keyword)
