from domain.clip import ClipState
from domain.pipeline_context import PipelineContext
from domain.stage import Stage, StageGroup


class CullStage(Stage):

    INPUT_CLIP_STATE = ClipState.ELIGIBLE
    OUTPUT_CLIP_STATE = ClipState.REJECTED
    STAGE_GROUP = StageGroup.DISCOVER

    @property
    def name(self) -> str:
        return "<CULL>"

    def is_stage_enabled(self, ctx: PipelineContext) -> bool:
        return True

    def run(self, ctx: PipelineContext) -> None:
        # TEMP: Sorting by view_count and truncating to target_count for testing
        eligible_count = ctx.clip.count_clips_in_state(ClipState.ELIGIBLE)
        candidates_needed = ctx.run_config.CANDIDATE_GOAL - eligible_count
        if candidates_needed <= 0:
            return

        discovered = sorted(
            ctx.clip.clips_in_state(ClipState.DISCOVERED),
            key=lambda c: c.metadata.view_count or 0,
            reverse=True,
        )

        for clip in discovered[:candidates_needed]:
            clip.state = ClipState.ELIGIBLE
