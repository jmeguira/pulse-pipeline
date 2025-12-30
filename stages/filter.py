from domain.clip import ClipState
from domain.pipeline_context import PipelineContext
from domain.stage import Stage, StageGroup


class FilterStage(Stage):

    INPUT_CLIP_STATE = ClipState.ELIGIBLE
    OUTPUT_CLIP_STATE = ClipState.FILTERED
    STAGE_GROUP = StageGroup.DISCOVER

    @property
    def name(self) -> str:
        return "<FILTER>"

    def is_stage_enabled(self, ctx: PipelineContext) -> bool:
        return True

    def run(self, ctx: PipelineContext) -> None:
        eligible_clips = ctx.clip.clips_in_state(ClipState.ELIGIBLE)

        for clip in eligible_clips:
            if clip.metadata.duration < ctx.run_config.DURATION_MIN:
                clip.state = ClipState.FILTERED
                clip.status_reason = f"too_short: min={ctx.run_config.DURATION_MIN}"
                continue

            if clip.metadata.duration > ctx.run_config.DURATION_MAX:
                clip.state = ClipState.FILTERED
                clip.status_reason = f"too_long: max={ctx.run_config.DURATION_MAX}"
                continue

            if clip.metadata.is_age_restricted:
                clip.state = ClipState.FILTERED
                clip.status_reason = "age_restricted"
                continue

            if clip.metadata.is_region_blocked_us:
                clip.state = ClipState.FILTERED
                clip.status_reason = "region_blocked_us"
                continue

            if not clip.metadata.is_public:
                clip.state = ClipState.FILTERED
                clip.status_reason = "private"
                continue

            if ctx.run_config.FILTER_LICENSED_CONTENT and clip.metadata.is_licensed:
                clip.state = ClipState.FILTERED
                clip.status_reason = "licensed"
                continue
