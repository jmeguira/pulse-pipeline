from dataclasses import dataclass, field
from typing import List

from domain.clip import Clip, ClipState
from domain.run_config import RunConfig


@dataclass
class AcquireContext:
    cursor: str | None = None
    pages_processed: int = 0


@dataclass
class ClipContext:
    """Holds state for clip domain objects"""

    clips: List[Clip] = field(default_factory=list)

    @property
    def eligible_clips(self) -> List[Clip]:
        return self.clips_in_state(state=ClipState.ELIGIBLE)

    @property
    def eligible_count(self) -> int:
        return sum(1 for c in self.clips if c.state == ClipState.ELIGIBLE)

    def clips_in_state(self, state: ClipState) -> List[Clip]:
        return [c for c in self.clips if c.state == state]

    def count_in_state(self, state: ClipState) -> int:
        return sum(1 for c in self.clips if c.state == state)

    def clips_not_in_state(self, state: ClipState) -> List[Clip]:
        return [c for c in self.clips if c.state != state]


@dataclass
class PipelineContext:
    run_config: RunConfig
    acquire: AcquireContext
    clip: ClipContext
