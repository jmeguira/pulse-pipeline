import os
from pathlib import Path

from dotenv import load_dotenv

from config.keyword_config import KEYWORD_CONFIG
from domain.clip import ClipState
from domain.pipeline_context import PipelineContext, AcquireContext, ClipContext
from domain.run_config import RunConfig
from domain.stage import StageGroup, Stage
from stages.compile import CompileStage
from stages.cull import CullStage
from stages.discover import DiscoverStage
from stages.download import DownloadStage
from stages.filter import FilterStage
from stages.persist import PersistStage
from stages.score import ScoreStage
from stages.select import SelectStage
from stages.transform import TransformStage
from utils.flag_utils import load_flags
from utils.utils import (
    prompt_keyword_choice,
    prompt_date_range,
    prompt_target_count,
    get_date_range_str,
)

load_dotenv()

# --- Fetch/Discover
MAX_PAGES = int(os.getenv("MAX_PAGES", 100))
OVERSAMPLE = int(os.getenv("OVERSAMPLE", 10))
ORDER = os.getenv("ORDER", "relevance")
RELEVANCE_LANGUAGE = os.getenv("RELEVANCE_LANGUAGE", "en")
REGION_CODE = os.getenv("REGION_CODE", "us")

# --- Download
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
if not YOUTUBE_API_KEY:
    raise RuntimeError("Missing YOUTUBE_API_KEY. Set it in .env or your environment.")

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

YDL_OPTS_BASE = {
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

# --- Preprocessing
ENABLE_LUFS = os.getenv("ENABLE_LUFS", "true").lower() == "true"
TARGET_LUFS = float(os.getenv("TARGET_LUFS", -14.0))

# --- Compilation / Output ---
OUTPUT_WIDTH = int(os.getenv("OUTPUT_WIDTH", 1920))
OUTPUT_HEIGHT = int(os.getenv("OUTPUT_HEIGHT", 1080))
OUTPUT_BASE_PATH = os.getenv("OUTPUT_BASE_PATH", "downloads/")
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
    output_full_path = os.path.join(
        OUTPUT_BASE_PATH, keyword, get_date_range_str(start_date, end_date)
    )

    keyword_config = KEYWORD_CONFIG[keyword]
    if not keyword_config:
        raise ValueError(f"No keyword config defined for '{keyword}'")

    return RunConfig(
        KEYWORD=keyword,
        KEYWORD_CONFIG=keyword_config,
        TARGET_COUNT=target_count,
        PUBLISHED_AFTER=start_date,
        PUBLISHED_BEFORE=end_date,
        BATCH_SIZE=50,
        MAX_PAGES=MAX_PAGES,
        ORDER=ORDER,
        OVERSAMPLE=OVERSAMPLE,
        RELEVANCE_LANGUAGE=RELEVANCE_LANGUAGE,
        REGION_CODE=REGION_CODE,
        CANDIDATE_GOAL=target_count * OVERSAMPLE,
        YOUTUBE_API_KEY=YOUTUBE_API_KEY,
        YDL_OPTS=YDL_OPTS_BASE,
        ENABLE_LUFS=ENABLE_LUFS,
        TARGET_LUFS=TARGET_LUFS,
        OUTPUT_WIDTH=OUTPUT_WIDTH,
        OUTPUT_HEIGHT=OUTPUT_HEIGHT,
        OUTPUT_BASE_PATH=OUTPUT_BASE_PATH,
        OUTPUT_FULL_PATH=output_full_path,
        TARGET_FPS=TARGET_FPS,
        TITLE_CARD_PATH=TITLE_CARD_PATH,
        TRANSITION_SOUND_PATH=TRANSITION_SOUND_PATH,
        TRANSITION_DURATION=TRANSITION_DURATION,
        THUMBNAIL_WIDTH=THUMBNAIL_WIDTH,
        THUMBNAIL_HEIGHT=THUMBNAIL_HEIGHT,
        THUMBNAIL_LOGO_PATH=THUMBNAIL_LOGO_PATH,
    )


def is_group_enabled(ctx: PipelineContext, stage: Stage, group: StageGroup) -> bool:
    if ctx.flags.dry_run:
        return stage.STAGE_GROUP is group
    return True


def main_pipeline(ctx: PipelineContext) -> None:
    acquire_stages = [
        DiscoverStage(),
        FilterStage(),
        CullStage(),
    ]

    assemble_stages = [
        ScoreStage(),
        SelectStage(),
        DownloadStage(),
        TransformStage(),
        CompileStage(),
        PersistStage(),
    ]

    # teardown_phase = [CleanStage()]

    while True:
        for stage in acquire_stages:
            stage.execute(ctx)

        if ctx.clip.count_clips_in_state(ClipState.ELIGIBLE) >= ctx.run_config.CANDIDATE_GOAL:
            print(
                f"Candidate goal reached: {ctx.clip.eligible_count}/{ctx.run_config.CANDIDATE_GOAL} "
                f"(target_count={ctx.run_config.TARGET_COUNT}, oversample={ctx.run_config.OVERSAMPLE})"
            )
            break

        if ctx.acquire.pages_processed >= ctx.run_config.MAX_PAGES:
            print(
                f"Stopping discovery: hit MAX_PAGES={ctx.run_config.MAX_PAGES} with"
                f" {ctx.clip.eligible_count}/{ctx.run_config.CANDIDATE_GOAL} candidates."
                f" Likely: narrow date window, strict gate, or low-signal keyword."
            )
            break

        if not ctx.acquire.cursor:
            print(
                f"End of search results (no nextPageToken) at page {ctx.acquire.pages_processed}. "
                f"Collected {ctx.clip.eligible_count}/{ctx.run_config.CANDIDATE_GOAL} candidates."
            )
            break

    for stage in assemble_stages:
        if ctx.flags.dry_run:
            if not is_group_enabled(ctx, stage, StageGroup.DISCOVER):
                print(f"⏭ Skipping stage: {stage.name}")
                continue
        stage.execute(ctx)


if __name__ == "__main__":
    run_config = build_run_config(list(KEYWORD_CONFIG.keys()))
    flags = load_flags(Path("flags.json"))
    print(flags)
    context = PipelineContext(
        run_config=run_config, acquire=AcquireContext(), clip=ClipContext(), flags=flags
    )
    main_pipeline(context)
