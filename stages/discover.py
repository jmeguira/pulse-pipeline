from datetime import datetime, timezone, timedelta

import isodate
from googleapiclient.discovery import build

from domain.clip import ClipState, Clip, ClipMetadata, ClipSource
from domain.stage import Stage
from utils.utils import keyword_in_title_or_description


class DiscoverStage(Stage):
    OUTPUT_CLIP_STATE = ClipState.ELIGIBLE

    @property
    def name(self):
        return "Discover YouTube Shorts"

    def candidate_goal(self) -> int:
        return self.context.run_config.target_count * self.context.run_config.OVERSAMPLE

    def should_run(self):
        if len(self.clips_in_state(self.OUTPUT_CLIP_STATE)) >= self.candidate_goal():
            return False
        return True

    def run(self):
        keyword = self.context.run_config.keyword
        target_count = self.context.run_config.target_count
        candidate_goal = self.candidate_goal()
        max_pages = self.context.run_config.MAX_PAGES
        batch_size = self.context.run_config.batch_size
        published_after = datetime.combine(
            self.context.run_config.published_after,
            datetime.min.time(),
            tzinfo=timezone.utc,
        ).isoformat()
        published_before = datetime.combine(
            self.context.run_config.published_before + timedelta(days=1),
            datetime.min.time(),
            tzinfo=timezone.utc,
        ).isoformat()

        print(
            f"🔍 Fetching Shorts for '{keyword}' | target_count: '{target_count}' | candidate_goal: '{candidate_goal}'"
        )

        candidate_pool = self.clips_in_state(state=self.OUTPUT_CLIP_STATE).copy()
        seen_ids = {c.metadata.id for c in candidate_pool}

        youtube = build("youtube", "v3", developerKey=self.context.run_config.YOUTUBE_API_KEY)
        page = 1
        evaluated = 0
        accepted = 0
        next_page_token = None
        while True:
            if len(candidate_pool) >= candidate_goal:
                break

            if page > max_pages:
                print(
                    f"🛑 Stopping discovery: hit MAX_PAGES={max_pages} with"
                    f" {len(candidate_pool)}/{candidate_goal} candidates. "
                    f"Likely: narrow date window, strict gate, or low-signal keyword."
                )
                break

            print(
                f"  ➤ Page {page}/{max_pages} | candidates: {len(candidate_pool)}/{candidate_goal} |"
                f" target_count={target_count}"
            )

            try:
                search_resp = (
                    youtube.search()
                    .list(
                        q=keyword,
                        type="video",
                        part="id",
                        maxResults=min(batch_size, 50),
                        publishedAfter=published_after,
                        publishedBefore=published_before,
                        order="viewCount",
                        pageToken=next_page_token,
                    )
                    .execute()
                )
            except Exception as e:
                print(f"❌ YouTube search failed on page {page} (token={next_page_token}): {e}")
                break

            video_ids = []
            for item in search_resp.get("items", []):
                video_id = item.get("id", {}).get("videoId")
                if video_id:
                    video_ids.append(video_id)

            video_ids = video_ids[:50]

            if not video_ids:
                print(
                    f"🛑 No results returned on page {page} (token={next_page_token}). "
                    f"Stopping with {len(candidate_pool)}/{candidate_goal} candidates."
                )
                break

            try:
                videos_resp = (
                    youtube.videos()
                    .list(
                        part="snippet,contentDetails,statistics",
                        id=",".join(video_ids),
                    )
                    .execute()
                )
            except Exception as e:
                print(f"❌ videos.list failed for {len(video_ids)} ids on page {page}: {e}")
                break

            for video in videos_resp.get("items", []):
                evaluated += 1
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
                seen = video["id"] in seen_ids

                if duration_sec <= 60 and not age_restricted and keyword_match and not seen:
                    accepted += 1
                    candidate_pool.append(
                        Clip(
                            source=ClipSource.YOUTUBE,
                            state=ClipState.ELIGIBLE,
                            metadata=ClipMetadata(
                                id=video["id"],
                                title=video["snippet"]["title"],
                                uploader=video["snippet"]["channelTitle"],
                                channel_id=video["snippet"]["channelId"],
                                url=f"https://www.youtube.com/watch?v={video['id']}",
                                upload_date=video["snippet"]["publishedAt"],
                                view_count=int(video["statistics"].get("viewCount", 0)),
                                duration=duration_sec,
                            ),
                        )
                    )
                    seen_ids.add(video["id"])

                    if len(candidate_pool) >= candidate_goal:
                        print(
                            f"✅ Candidate goal reached: {len(candidate_pool)}/{candidate_goal} "
                            f"(target_count={target_count}, oversample={self.context.run_config.OVERSAMPLE})"
                        )
                        break

            next_page_token = search_resp.get("nextPageToken")

            if next_page_token is None:
                print(
                    f"🛑 End of search results (no nextPageToken) at page {page}. "
                    f"Collected {len(candidate_pool)}/{candidate_goal} candidates."
                )
                break

            page += 1

        ineligible_clips = self.clips_not_in_state(self.OUTPUT_CLIP_STATE)
        self.context.clips = ineligible_clips + candidate_pool
        print(
            f"📊 Discovery stats: evaluated={evaluated}, accepted={accepted}"
            f", accept_rate={(accepted/max(evaluated,1)):.1%}"
        )
