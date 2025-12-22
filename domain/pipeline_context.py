from dataclasses import dataclass, field
from typing import List

from domain.clip import Clip, ClipState
from domain.run_config import RunConfig


@dataclass
class QueryContext:
    cursor: str | None = None
    pages_fetched: int = 0


@dataclass
class ClipContext:
    """Holds state for clip domain objects"""

    clips: List[Clip] = field(default_factory=list)

    def clips_in_state(self, state: ClipState) -> List[Clip]:
        return [c for c in self.clips if c.state == state]

    def count_in_state(self, state: ClipState) -> int:
        return sum(1 for c in self.clips if c.state == state)

    def clips_not_in_state(self, state: ClipState) -> List[Clip]:
        return [c for c in self.clips if c.state != state]


@dataclass
class PipelineContext:
    run_config: RunConfig
    query_ctx: QueryContext
    clip_ctx: ClipContext
