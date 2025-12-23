from datetime import datetime, timezone, timedelta

import isodate
from googleapiclient.discovery import build

from domain.clip import ClipState, Clip, ClipMetadata, ClipSource
from domain.pipeline_context import PipelineContext
from domain.stage import Stage


def build_query(ctx: PipelineContext) -> str:
    include = " ".join(ctx.run_config.KEYWORD_CONFIG.query_include)
    exclude = " ".join(f"-{term}" for term in ctx.run_config.KEYWORD_CONFIG.query_exclude)
    return f"{include} {exclude}".strip()


class DiscoverStage(Stage):
    OUTPUT_CLIP_STATE = ClipState.ELIGIBLE

    @property
    def name(self):
        return "Discover YouTube Shorts"

    def should_run(self, ctx: PipelineContext) -> bool:
        if ctx.clip.eligible_count >= ctx.run_config.CANDIDATE_GOAL:
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

        candidate_pool = ctx.clip.eligible_clips.copy()

        youtube = build("youtube", "v3", developerKey=ctx.run_config.YOUTUBE_API_KEY)

        print(
            f"  ➤ Page {ctx.acquire.pages_processed}/{max_pages} | candidates: {len(candidate_pool)}/{candidate_goal} |"
            f" target_count={target_count}"
        )

        try:
            search_resp = (
                youtube.search()
                .list(
                    q=build_query(ctx),
                    type="video",
                    part="id",
                    maxResults=min(batch_size, 50),
                    publishedAfter=published_after,
                    publishedBefore=published_before,
                    videoDuration="short",
                    order=ctx.run_config.ORDER,
                    relevanceLanguage=ctx.run_config.RELEVANCE_LANGUAGE,
                    regionCode=ctx.run_config.REGION_CODE,
                    pageToken=ctx.acquire.cursor,
                )
                .execute()
            )
        except Exception as e:
            raise Exception(f"❌ YouTube search failed on page {ctx.acquire.pages_processed + 1} (token={ctx.acquire.cursor}): {e}")

        ctx.acquire.pages_processed += 1
        ctx.acquire.cursor = search_resp.get("nextPageToken")

        video_ids = []
        for item in search_resp.get("items", []):
            video_id = item.get("id", {}).get("videoId")
            if video_id:
                video_ids.append(video_id)

        video_ids = video_ids[:50]

        if not video_ids:
            raise Exception(
                f"🛑 No results returned on page {ctx.acquire.pages_processed} (token={ctx.acquire.cursor}). "
                f"Stopping with {len(candidate_pool)}/{candidate_goal} candidates."
            )

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
            raise Exception(f"❌ videos.list failed for {len(video_ids)} ids on page {ctx.acquire.pages_processed}: {e}")

        for video in videos_resp.get("items", []):
            id = video["id"]
            title = video["snippet"]["title"]
            uploader = video["snippet"]["channelTitle"]
            channel_id = video["snippet"]["channelId"]
            url = f"https://www.youtube.com/watch?v={id}"
            upload_date = video["snippet"]["publishedAt"]
            view_count = video["statistics"]["viewCount"]
            duration_sec = int(
                isodate.parse_duration(video["contentDetails"]["duration"]).total_seconds()
            )
            age_restricted = (
                video["contentDetails"].get("contentRating", {}).get("ytRating")
                == "ytAgeRestricted"
            )
            description = video["snippet"].get("description", "").lower()

            candidate_pool.append(
                Clip(
                    source=ClipSource.YOUTUBE,
                    state=ClipState.ELIGIBLE,
                    metadata=ClipMetadata(
                        id=id,
                        title=title,
                        description=description,
                        uploader=uploader,
                        channel_id=channel_id,
                        url=url,
                        upload_date=upload_date,
                        view_count=view_count,
                        duration=duration_sec,
                        age_restricted=age_restricted,
                    ),
                )
            )
            if len(candidate_pool) >= candidate_goal:
                print(
                    f"✅ Candidate goal reached: {len(candidate_pool)}/{candidate_goal} "
                    f"(target_count={target_count}, oversample={ctx.run_config.OVERSAMPLE})"
                )
                break

        ineligible_clips = ctx.clip.clips_not_in_state(state=ClipState.ELIGIBLE)
        ctx.clips = ineligible_clips + candidate_pool
