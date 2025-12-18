from dataclasses import dataclass, field
from typing import List

from domain.clip import Clip
from domain.run_config import RunConfig


@dataclass
class PipelineContext:
    run_config: RunConfig
    clips: List[Clip] = field(default_factory=list)
