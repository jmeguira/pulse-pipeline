from domain.clip import ClipState
from domain.pipeline_context import PipelineContext
from domain.stage import Stage


class FilterStage(Stage):

    INPUT_CLIP_STATE = ClipState.ELIGIBLE
    OUTPUT_CLIP_STATE: ClipState.REJECTED

    @property
    def name(self) -> str:
        return "<FILTER>"

    def should_run(self, ctx: PipelineContext) -> bool:
        return True

    def run(self, ctx: PipelineContext) -> None:
        pass


"""
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
"""
