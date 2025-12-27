from domain.pipeline_context import PipelineContext
from domain.stage import Stage, StageGroup


class CleanStage(Stage):
    STAGE_GROUP = StageGroup.ASSEMBLE

    @property
    def name(self):
        return "<CLEAN>"

    def is_stage_enabled(self, ctx: PipelineContext) -> bool:
        return True

    def run(self, ctx: PipelineContext) -> None:
        pass
