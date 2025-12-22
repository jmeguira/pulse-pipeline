from domain.clip import ClipState
from domain.pipeline_context import PipelineContext
from domain.stage import Stage


class CullStage(Stage):

    INPUT_CLIP_STATE: ClipState | None = None
    OUTPUT_CLIP_STATE: ClipState | None = None

    @property
    def name(self) -> str:
        return "cull stage"

    def should_run(self, ctx: PipelineContext) -> bool:
        return True

    def run(self, ctx: PipelineContext) -> None:
        pass
