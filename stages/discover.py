from datetime import datetime, timezone, timedelta

import isodate
from googleapiclient.discovery import build

from domain.clip import ClipState, Clip, ClipMetadata, ClipSource
from domain.pipeline_context import PipelineContext
from domain.stage import Stage
from utils.utils import keyword_in_title_or_description


class DiscoverStage(Stage):
    OUTPUT_CLIP_STATE = ClipState.ELIGIBLE

    @property
    def name(self):
        return "Discover YouTube Shorts"

    def should_run(self, ctx: PipelineContext) -> bool:
        if ctx.clip_ctx.count_in_state(ClipState.ELIGIBLE) >= ctx.run_config.CANDIDATE_GOAL:
            return False
        return True

    def run(self, ctx: PipelineContext) -> None:
        keyword = ctx.run_config.KEYWORD
        target_count = ctx.run_config.TARGET_COUNT
        candidate_goal = ctx.run_config.CANDIDATE_GOAL
        max_pages = ctx.run_config.MAX_PAGES
        batch_size = ctx.run_config.BATCH_SIZE
        published_after = datetime.combine(
            ctx.run_config.PUBLISHED_AFTER,
            datetime.min.time(),
            tzinfo=timezone.utc,
        ).isoformat()
        published_before = datetime.combine(
            ctx.run_config.PUBLISHED_BEFORE + timedelta(days=1),
            datetime.min.time(),
            tzinfo=timezone.utc,
        ).isoformat()

        print(
            f"🔍 Fetching Shorts for '{keyword}' | target_count: '{target_count}' | candidate_goal: '{candidate_goal}'"
        )

        candidate_pool = ctx.clip_ctx.clips_in_state(state=self.OUTPUT_CLIP_STATE).copy()
        seen_ids = {c.metadata.id for c in candidate_pool}

        youtube = build("youtube", "v3", developerKey=ctx.run_config.YOUTUBE_API_KEY)
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
                            f"(target_count={target_count}, oversample={ctx.run_config.OVERSAMPLE})"
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

        ineligible_clips = ctx.clip_ctx.clips_not_in_state(self.OUTPUT_CLIP_STATE)
        ctx.clips = ineligible_clips + candidate_pool
        print(
            f"📊 Discovery stats: evaluated={evaluated}, accepted={accepted}"
            f", accept_rate={(accepted/max(evaluated,1)):.1%}"
        )
