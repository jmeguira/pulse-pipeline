from domain.clip import ClipState
from domain.pipeline_context import PipelineContext
from domain.stage import Stage


class SelectStage(Stage):

    INPUT_CLIP_STATE = ClipState.ELIGIBLE
    OUTPUT_CLIP_STATE = ClipState.SELECTED

    def name(self) -> str:
        return "<SELECT>"

    def should_run(self, ctx: PipelineContext) -> bool:
        return True

    def run(self, ctx: PipelineContext) -> None:
        eligible = sorted(
            ctx.clip.clips_in_state(ClipState.ELIGIBLE),
            key=lambda c: c.metadata.view_count or 0,
            reverse=True,
        )

        for clip in eligible[:ctx.run_config.TARGET_COUNT]:
            clip.state = ClipState.SELECTED
