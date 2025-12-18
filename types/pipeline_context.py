from dataclasses import dataclass, field
from typing import List

from types.clip import Clip
from types.run_config import RunConfig


@dataclass
class PipelineContext:
    run_config: RunConfig
    clips: List[Clip] = field(default_factory=list)
