from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from domain.clip import Clip, ClipState
from domain.run_config import RunConfig
from domain.runtime_flags import RuntimeFlags
from utils.flag_utils import load_flags


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

    def clips_not_in_state(self, state: ClipState) -> List[Clip]:
        return [c for c in self.clips if c.state != state]

    def count_clips_in_state(self, state: ClipState) -> int:
        return sum(1 for c in self.clips if c.state == state)

    def count_clips_by_state(self, compact: bool = True):
        state_counts = Counter(clip.state for clip in self.clips)

        if compact:
            parts = " ".join(f"{state.name}={count}" for state, count in state_counts.items())
            return f"[CANDIDATE POOL] {parts}"

        rtn = "[CANDIDATE POOL]"
        for state, count in state_counts.items():
            rtn += f"  {state.name}: {count}"
        return rtn


@dataclass
class PipelineContext:
    run_config: RunConfig
    acquire: AcquireContext
    clip: ClipContext
    flags: RuntimeFlags

    def __init__(
        self, run_config: RunConfig, acquire: AcquireContext, clip: ClipContext, flags: RuntimeFlags
    ):
        self.run_config = run_config
        self.acquire = acquire
        self.clip = clip
        self.flags = load_flags(Path("flags.json"))

    def __repr__(self):
        return (
            "[PIPELINE STATE] "
            f"keyword={self.run_config.KEYWORD} | "
            f"target={self.run_config.TARGET_COUNT} | "
            f"after={self.run_config.PUBLISHED_AFTER} | "
            f"before={self.run_config.PUBLISHED_BEFORE} | "
            f"cursor={self.acquire.cursor} | "
            f"pages={self.acquire.pages_processed} | "
            f"pool={self.clip.count_clips_by_state()}"
        )

    def debug_state(self) -> str:
        return "\n".join(
            [
                "-" * 48,
                "PIPELINE STATE",
                f"keyword           : {self.run_config.KEYWORD}",
                f"target_count      : {self.run_config.TARGET_COUNT}",
                f"published_after   : {self.run_config.PUBLISHED_AFTER}",
                f"published_before  : {self.run_config.PUBLISHED_BEFORE}",
                f"cursor            : {self.acquire.cursor}",
                f"pages_processed   : {self.acquire.pages_processed}",
                "clip_counts:",
                self.clip.count_clips_by_state(),
                "-" * 48,
            ]
        )
