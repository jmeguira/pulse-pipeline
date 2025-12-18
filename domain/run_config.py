from dataclasses import dataclass
from datetime import date

from config.keyword_config import KeywordConfig


@dataclass
class RunConfig:
    keyword: str
    keyword_config: KeywordConfig
    target_count: int
    published_after: date
    published_before: date
    enable_lufs: bool
    target_lufs: float
    batch_size: int
    YOUTUBE_API_KEY: str
    YDL_OPTS: dict
    # --- Compilation / Output ---
    OUTPUT_WIDTH: int
    OUTPUT_HEIGHT: int
    OUTPUT_BASE_PATH: str
    OUTPUT_FULL_PATH: str
    TARGET_FPS: int
    TITLE_CARD_PATH: str
    TRANSITION_SOUND_PATH: str
    TRANSITION_DURATION: float
    # --- Thumbnail Defaults ---
    THUMBNAIL_WIDTH: int
    THUMBNAIL_HEIGHT: int
    THUMBNAIL_LOGO_PATH: str
