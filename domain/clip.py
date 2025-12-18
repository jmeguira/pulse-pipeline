import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class ClipSource(str, Enum):
    YOUTUBE = "YouTube"
    REDDIT = "Reddit"


class ClipState(str, Enum):
    ELIGIBLE = "eligible"
    DOWNLOADED = "downloaded"
    PROCESSED = "processed"
    FAILED = "failed"


@dataclass
class ClipMetadata:
    id: str
    title: str
    uploader: str
    channel_id: str
    url: str
    upload_date: str
    view_count: int
    duration: int


class Clip:
    def __init__(
        self,
        source: ClipSource,
        state: ClipState,
        metadata: ClipMetadata,
        raw_path: Optional[Path] = None,
        processed_path: Optional[Path] = None,
    ):
        self.id = str(uuid.uuid4())
        self.source = source
        self.state = state
        self.metadata = metadata
        self.raw_path = raw_path
        self.processed_path = processed_path
        self.failure_reason: Optional[str] = None

    def set_state(self, new_state: ClipState, reason: Optional[str] = None):
        self.state = new_state
        if reason:
            self.failure_reason = reason

    def is_stage_ready(self, stage_state: ClipState) -> bool:
        return self.state == stage_state

    def __repr__(self):
        return f"<{self.source} Clip: state={self.state} id={self.id}>"
