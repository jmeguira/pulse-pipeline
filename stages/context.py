from dataclasses import dataclass, field
from typing import List, Dict, Any

from moviepy import VideoFileClip

from config.run_config import RunConfig


@dataclass
class PipelineContext:
    run_config: RunConfig
    videos: List[Dict[str, Any]] = field(default_factory=list)
    clips: List[VideoFileClip] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    filepaths: Dict[str, str] = field(default_factory=dict)
