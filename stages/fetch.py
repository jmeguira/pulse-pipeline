import os
from datetime import datetime, timezone, timedelta

import isodate
from googleapiclient.discovery import build

from types.clip import ClipState
from types.stage import Stage
from utils.utils import keyword_in_title_or_description


class FetchStage(Stage):
    OUTPUT_CLIP_STATE = ClipState.ELIGIBLE

    @property
    def name(self):
        return "Fetch YouTube Shorts"

    def should_run(self):
        # e.g., only run if no cached metadata exists
        return True

    def run(self):
        keyword = self.context.run_config.keyword
        target_count = self.context.run_config.target_count
        published_after = self.context.run_config.published_after
        published_before = self.context.run_config.published_before
        youtube = build("youtube", "v3", developerKey=self.context.run_config.YOUTUBE_API_KEY)
        clips_collected = []
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

        while len(clips_collected) < target_count:
            print(f"  ➤ Batch #{batch_number}, already collected: {len(clips_collected)}")

            try:
                search_resp = (
                    youtube.search()
                    .list(
                        q=keyword,
                        type="video",
                        part="id",
                        maxResults=self.context.run_config.batch_size,
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
                    clips_collected.append(
                        {
                            "id": video["id"],
                            "title": video["snippet"]["title"],
                            "uploader": video["snippet"]["channelTitle"],
                            "channel_id": video["snippet"]["channelId"],
                            "url": f"https://www.youtube.com/watch?v={video['id']}",
                            "upload_date": video["snippet"]["publishedAt"],
                            "view_count": int(video["statistics"].get("viewCount", 0)),
                            "duration": duration_sec,
                            "file_path": os.path.join(
                                self.context.run_config.OUTPUT_FULL_PATH, f"{video['id']}.mp4"
                            ),
                        }
                    )

            next_page_token = search_resp.get("nextPageToken")
            if not next_page_token:
                break

            batch_number += 1

        clips_collected.sort(key=lambda x: x["view_count"], reverse=True)
        self.context.videos = clips_collected[:target_count]
