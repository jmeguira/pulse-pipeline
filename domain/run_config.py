from dataclasses import dataclass
from datetime import date

from config.keyword_config import KeywordConfig


@dataclass
class RunConfig:
    KEYWORD: str
    KEYWORD_CONFIG: KeywordConfig
    TARGET_COUNT: int
    PUBLISHED_AFTER: date
    PUBLISHED_BEFORE: date
    ENABLE_LUFS: bool
    TARGET_LUFS: float
    # --- Acquisition Loop --- #
    BATCH_SIZE: int
    MAX_PAGES: int
    ORDER: str
    OVERSAMPLE: int
    RELEVANCE_LANGUAGE: str
    REGION_CODE: str
    CANDIDATE_GOAL: int
    YOUTUBE_API_KEY: str
    YDL_OPTS: dict
    # --- Compilation / Output --- #
    OUTPUT_WIDTH: int
    OUTPUT_HEIGHT: int
    OUTPUT_BASE_PATH: str
    OUTPUT_FULL_PATH: str
    TARGET_FPS: int
    TITLE_CARD_PATH: str
    TRANSITION_SOUND_PATH: str
    TRANSITION_DURATION: float
    # --- Thumbnail Defaults --- #
    THUMBNAIL_WIDTH: int
    THUMBNAIL_HEIGHT: int
    THUMBNAIL_LOGO_PATH: str
