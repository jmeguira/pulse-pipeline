from abc import ABC, abstractmethod

from domain.clip import ClipState
from domain.pipeline_context import PipelineContext


class Stage(ABC):
    """Base class for all stages in the pipeline."""

    INPUT_CLIP_STATE: ClipState | None = None
    OUTPUT_CLIP_STATE: ClipState | None = None

    def __init__(self, context: PipelineContext):
        self.context = context

    def clips_in_state(self, state: ClipState):
        return [c for c in self.context.clips if c.state == state]

    def clips_not_in_state(self, state: ClipState):
        return [c for c in self.context.clips if c.state != state]

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable stage name."""
        pass

    @abstractmethod
    def should_run(self) -> bool:
        """Return True if this stage should execute."""
        return True

    @abstractmethod
    def run(self):
        """Stage-specific behavior."""
        pass

    def execute(self):
        """Run the stage if should_run() is True."""
        if self.should_run():
            print(f"▶ Running stage: {self.name}")
            self.run()
        else:
            print(f"⏭ Skipping stage: {self.name}")
