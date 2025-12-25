from abc import ABC, abstractmethod

from domain.clip import ClipState
from domain.pipeline_context import PipelineContext


class Stage(ABC):
    """Base class for all stages in the pipeline."""

    INPUT_CLIP_STATE: ClipState | None = None
    OUTPUT_CLIP_STATE: ClipState | None = None

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable stage name."""
        pass

    @abstractmethod
    def should_run(self, ctx: PipelineContext) -> bool:
        """Return True if this stage should execute."""
        return True

    @abstractmethod
    def run(self, ctx: PipelineContext):
        """Stage-specific behavior."""
        raise NotImplementedError

    def execute(self, ctx: PipelineContext) -> None:
        """Run the stage if should_run() is True."""
        if self.should_run(ctx):
            print(f"▶ Running stage: {self.name}")
            self.run(ctx)
            print(ctx)
        else:
            print(f"⏭ Skipping stage: {self.name}")
