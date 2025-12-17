from abc import ABC, abstractmethod

from stages.context import PipelineContext


class Stage(ABC):
    """Base class for all stages in the pipeline."""

    def __init__(self, context: PipelineContext):
        self.context = context

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
