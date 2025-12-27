from domain.clip import ClipState
from domain.pipeline_context import PipelineContext
from domain.stage import Stage, StageGroup


class ScoreStage(Stage):
    INPUT_CLIP_STATE = ClipState.SELECTED
    # OUTPUT_CLIP_STATE = ClipState.SCORED
    STAGE_GROUP = StageGroup.DISCOVER

    @property
    def name(self) -> str:
        return "<SCORE>"

    def is_stage_enabled(self, ctx: PipelineContext) -> bool:
        return True

    def run(self, ctx: PipelineContext) -> None:
        pass
