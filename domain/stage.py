from abc import ABC, abstractmethod
from enum import Enum

from domain.clip import ClipState
from domain.pipeline_context import PipelineContext


class StageGroup(str, Enum):
    DISCOVER = "discover"
    ASSEMBLE = "assemble"
    PERSIST = "persist"


class Stage(ABC):
    """Base class for all stages in the pipeline."""

    INPUT_CLIP_STATE: ClipState | None = None
    OUTPUT_CLIP_STATE: ClipState | None = None
    STAGE_GROUP: StageGroup

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if not hasattr(cls, "STAGE_GROUP"):
            allowed = " | ".join(g.value for g in StageGroup)
            raise TypeError(f"{cls.__name__} must define STAGE_GROUP " f"({allowed})")

        if not isinstance(cls.STAGE_GROUP, StageGroup):
            raise TypeError(
                f"{cls.__name__}.STAGE_GROUP must be a StageGroup enum, " f"got {cls.STAGE_GROUP}"
            )

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable stage name."""
        pass

    @abstractmethod
    def is_stage_enabled(self, ctx: PipelineContext) -> bool:
        """Return True if this stage is ready for execution."""

    def is_group_enabled(self, group: StageGroup) -> bool:
        """Return True if this stage should be executed."""
        return self.STAGE_GROUP == group

    @abstractmethod
    def run(self, ctx: PipelineContext):
        """Stage-specific behavior."""
        raise NotImplementedError

    def execute(self, ctx: PipelineContext) -> None:
        """Run the stage if should_run() is True."""
        if self.is_stage_enabled(ctx):
            self.run(ctx)
