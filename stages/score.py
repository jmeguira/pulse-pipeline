from domain.clip import ClipState
from domain.pipeline_context import PipelineContext
from domain.stage import Stage


class ScoreStage(Stage):
    INPUT_CLIP_STATE = ClipState.SELECTED
    # OUTPUT_CLIP_STATE = ClipState.SCORED

    @property
    def name(self) -> str:
        """Score Stage"""
        return "<SCORE>"

    def should_run(self, ctx: PipelineContext) -> bool:
        return True

    def run(self, ctx: PipelineContext) -> None:
        pass
