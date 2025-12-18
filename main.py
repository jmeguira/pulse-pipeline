import os

from dotenv import load_dotenv

from config.keyword_config import KEYWORD_CONFIG
from config.run_config import RunConfig
from stages.compile import CompileStage
from stages.context import PipelineContext
from stages.download import DownloadStage
from stages.fetch import FetchStage
from stages.metadata import MetadataStage
from stages.preprocess import PreprocessStage
from utils.utils import (
    prompt_keyword_choice,
    prompt_date_range,
    prompt_target_count,
    get_date_range_str,
)

"""Load environment variables"""
load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
if not YOUTUBE_API_KEY:
    raise RuntimeError("Missing YOUTUBE_API_KEY. Set it in .env or your environment.")

ENABLE_LUFS = os.getenv("ENABLE_LUFS", "true").lower() == "true"
TARGET_LUFS = float(os.getenv("TARGET_LUFS", -14.0))

YDL_FORMAT = os.getenv("YDL_FORMAT", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best")
YDL_NO_PLAYLIST = os.getenv("YDL_NO_PLAYLIST", "true").lower() == "true"
YDL_IGNORE_ERRORS = os.getenv("YDL_IGNORE_ERRORS", "true").lower() == "true"
YDL_COOKIEFILE = os.getenv("YDL_COOKIEFILE", "cookies.txt")
YDL_RETRIES = int(os.getenv("YDL_RETRIES", 3))
YDL_SLEEP_INTERVAL = float(os.getenv("YDL_SLEEP_INTERVAL", 0))
YDL_MAX_SLEEP_INTERVAL = float(os.getenv("YDL_MAX_SLEEP_INTERVAL", 5))
YDL_MERGE_FORMAT = os.getenv("YDL_MERGE_FORMAT", "mp4")
YDL_AGE_LIMIT = int(os.getenv("YDL_AGE_LIMIT", 18))
YDL_QUIET = os.getenv("YDL_QUIET", "true").lower() == "true"
YDL_NO_WARNINGS = os.getenv("YDL_NO_WARNINGS", "true").lower() == "true"

ydl_opts_base = {
    "format": YDL_FORMAT,
    "noplaylist": YDL_NO_PLAYLIST,
    "ignoreerrors": YDL_IGNORE_ERRORS,
    "cookiefile": YDL_COOKIEFILE,
    "retries": YDL_RETRIES,
    "sleep_interval_requests": YDL_SLEEP_INTERVAL,
    "max_sleep_interval": YDL_MAX_SLEEP_INTERVAL,
    "merge_output_format": YDL_MERGE_FORMAT,
    "age_limit": YDL_AGE_LIMIT,
    "quiet": YDL_QUIET,
    "no_warnings": YDL_NO_WARNINGS,
}

# --- Compilation / Output ---
OUTPUT_WIDTH = int(os.getenv("OUTPUT_WIDTH", 1920))
OUTPUT_HEIGHT = int(os.getenv("OUTPUT_HEIGHT", 1080))
OUTPUT_BASE_PATH = os.getenv("OUTPUT_BASE_PATH", "downloads/")
OUTPUT_FULL_PATH = os.path.join(
    OUTPUT_BASE_PATH,
)
TARGET_FPS = int(os.getenv("TARGET_FPS", 30))
TITLE_CARD_PATH = os.getenv("TITLE_CARD_PATH", "title_card.mp4")
TRANSITION_SOUND_PATH = os.getenv("TRANSITION_SOUND_PATH", "pop.wav")
TRANSITION_DURATION = float(os.getenv("TRANSITION_DURATION", 1.0))

# --- Video / Thumbnail Defaults ---
THUMBNAIL_WIDTH = int(os.getenv("THUMBNAIL_WIDTH", 1280))
THUMBNAIL_HEIGHT = int(os.getenv("THUMBNAIL_HEIGHT", 720))
THUMBNAIL_LOGO_PATH = os.getenv("THUMBNAIL_LOGO_PATH", "assets/logo.png")


def build_run_config(keyword_choices: list[str]) -> RunConfig:
    keyword = prompt_keyword_choice(keyword_choices)
    target_count = prompt_target_count()
    start_date, end_date = prompt_date_range()
    OUTPUT_FULL_PATH = os.path.join(
        OUTPUT_BASE_PATH, keyword, get_date_range_str(start_date, end_date)
    )

    keyword_config = KEYWORD_CONFIG[keyword]
    if not keyword_config:
        raise ValueError(f"No keyword config defined for '{keyword}'")

    return RunConfig(
        keyword=keyword,
        keyword_config=keyword_config,
        target_count=target_count,
        published_after=start_date,
        published_before=end_date,
        enable_lufs=ENABLE_LUFS,
        target_lufs=TARGET_LUFS,
        batch_size=50,
        YOUTUBE_API_KEY=YOUTUBE_API_KEY,
        YDL_OPTS=ydl_opts_base,
        OUTPUT_WIDTH=OUTPUT_WIDTH,
        OUTPUT_HEIGHT=OUTPUT_HEIGHT,
        OUTPUT_BASE_PATH=OUTPUT_BASE_PATH,
        OUTPUT_FULL_PATH=OUTPUT_FULL_PATH,
        TARGET_FPS=TARGET_FPS,
        TITLE_CARD_PATH=TITLE_CARD_PATH,
        TRANSITION_SOUND_PATH=TRANSITION_SOUND_PATH,
        TRANSITION_DURATION=TRANSITION_DURATION,
        THUMBNAIL_WIDTH=THUMBNAIL_WIDTH,
        THUMBNAIL_HEIGHT=THUMBNAIL_HEIGHT,
        THUMBNAIL_LOGO_PATH=THUMBNAIL_LOGO_PATH,
    )


def main_pipeline(context: PipelineContext):
    stages = [
        FetchStage(context),
        DownloadStage(context),
        PreprocessStage(context),
        CompileStage(context),
        MetadataStage(context),
    ]

    for stage in stages:
        if stage.should_run():
            stage.execute()


if __name__ == "__main__":
    run_config = build_run_config(list(KEYWORD_CONFIG.keys()))
    context = PipelineContext(run_config=run_config)
    main_pipeline(context)
