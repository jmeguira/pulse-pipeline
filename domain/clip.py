import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class ClipSource(str, Enum):
    YOUTUBE = "YouTube"
    REDDIT = "Reddit"


class ClipState(str, Enum):
    """
    Lifecycle state for a Clip within a single pipeline run.

    States are used to define stage contracts. A stage should operate on a specific
    state (or set of states) and advance clips forward.

    Typical progression (conceptual):
    - DISCOVERED  -> hydrated candidate metadata exists
    - FILTERED    -> filtered candidate
    - CULLED      -> deduped candidate
    - ELIGIBLE    -> passed hard gates (shape/constraints); still not "selected"
    - SELECTED    -> chosen for downstream execution (exactly target_count)
    - DOWNLOADED  -> raw media file exists locally
    - TRANSFORMED   -> transformed media artifact exists (normalized, trimmed, etc.)
    - COMPILED    -> incorporated into final compilation output
    - PERSISTED  -> persisted clip metadata and runlog

    Terminal / exceptional states:
    - FILTERED    -> failed a hard gate (reason should be recorded)
    - CULLED      -> failed a hard gate (reason should be recorded)_
    - FAILED      -> stage execution error (reason + stage should be recorded)

    Notes:
    - Eligibility is a *hard gate*; scoring/ranking should not reject clips.
    - Avoid implicit meaning: "eligible" is not the same as "selected."
    """

    DISCOVERED = "DISCOVERED"
    FILTERED = "FILTERED"
    CULLED = "CULLED"
    ELIGIBLE = "ELIGIBLE"
    SELECTED = "SELECTED"
    DOWNLOADED = "DOWNLOADED"
    TRANSFORMED = "TRANSFORMED"
    COMPILED = "COMPILED"
    PERSISTED = "PERSISTED"
    FAILED = "FAILED"


@dataclass
class ClipMetadata:
    """
    Metadata attached to a Clip.

    Contains identifiers and descriptive fields required for:
    - eligibility checks (duration, age restriction, topic match, etc.)
    - scoring/ranking (views, freshness, engagement signals, etc.)
    - downstream output (titles, attribution, URLs)

    The project prefers metadata-first reasoning: persist and operate on metadata
    before committing to heavyweight file operations.
    """

    id: str
    title: str
    description: str
    uploader: str
    channel_id: str
    url: str
    upload_date: str
    view_count: int
    duration: int
    is_age_restricted: bool
    is_region_blocked_us: bool
    is_public: bool
    is_licensed: bool

    def __repr__(self) -> str:
        title = (self.title[:60] + "…") if len(self.title) > 60 else self.title
        return (
            "ClipMetadata("
            f"id={self.id}, "
            f"title={title!r}, "
            f"uploader={self.uploader!r}, "
            f"upload_date={self.upload_date}, "
            f"url={self.url}, "
            f"view_count={self.view_count}, "
            f"duration={self.duration}s, "
            f"is_age_restricted={self.is_age_restricted}"
            f"is_region_blocked_us={self.is_region_blocked_us}"
            f"is_public={self.is_public}"
            f"is_licensed={self.is_licensed}"
            ")"
        )

    def to_dict(self) -> dict:
        title = (self.title[:60] + "…") if len(self.title) > 60 else self.title
        return {
            "id": self.id[:8],
            "title": title,
            "uploader": self.uploader,
            "upload_date": self.upload_date,
            "url": self.url,
            "view_count": self.view_count,
            "duration": self.duration,
            "is_age_restricted": self.is_age_restricted,
            "is_region_blocked_us": self.is_region_blocked_us,
            "is_public": self.is_public,
            "is_licensed": self.is_licensed,
        }


class Clip:
    """
    Run-scoped domain object representing one candidate unit of content.

    A Clip is the central object in the pipeline. It carries:
    - `source`: where the clip came from (e.g., YouTube)
    - `state`: lifecycle position in the pipeline (ClipState)
    - `metadata`: immutable-ish descriptive fields used for eligibility/scoring/output
    - optional artifact paths produced by stages (downloaded file, processed file, etc.)

    Design intent:
    - Clips start as lightweight metadata and only become "heavy" (files on disk)
      after selection/execution stages.
    - ClipState defines which stages may operate on a clip.
    - Failures should be explicit via FAILED/REJECTED with recorded reasons.

    Recommended invariants:
    - Stages should only advance state once the output artifact exists.
    - Stages should not silently mutate unrelated fields; prefer explicit transitions.
    """

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
        self.status_reason: Optional[str] = None

    def set_state(self, new_state: ClipState, reason: Optional[str] = None):
        self.state = new_state
        if reason:
            self.status_reason = reason

    def is_stage_ready(self, stage_state: ClipState) -> bool:
        return self.state == stage_state

    def __repr__(self) -> str:
        return (
            f"<Clip "
            f"id={self.id[:8]} "
            f"state={self.state.name} "
            f"source={self.source.name} "
            f"raw={'Y' if self.raw_path else 'N'} "
            f"processed={'Y' if self.processed_path else 'N'} "
            f"status_reason={self.status_reason or '-'}"
            f"\nmetadata={self.metadata}>"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id[:8],
            "state": self.state.name,
            "source": self.source.name,
            "status_reason": self.status_reason,
            "metadata": self.metadata.to_dict(),
        }
