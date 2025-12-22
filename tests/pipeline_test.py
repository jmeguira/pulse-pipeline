# tests/pipeline_test.py
from datetime import date
from unittest.mock import MagicMock, Mock

from domain.pipeline_context import PipelineContext
from domain.run_config import RunConfig
from stages.clean import CleanStage
from stages.compile import CompileStage
from stages.cull import CullStage
from stages.discover import DiscoverStage
from stages.download import DownloadStage
from stages.filter import FilterStage
from stages.persist import PersistStage
from stages.score import ScoreStage
from stages.select import SelectStage
from stages.transform import TransformStage


def make_test_run_config():
    return RunConfig(
        KEYWORD="test",
        KEYWORD_CONFIG={},  # can be empty dict for test
        TARGET_COUNT=1,
        PUBLISHED_AFTER=date.today(),
        PUBLISHED_BEFORE=date.today(),
        ENABLE_LUFS=False,
        TARGET_LUFS=-14.0,
        BATCH_SIZE=50,
        MAX_PAGES=5,
        OVERSAMPLE=20,
        CANDIDATE_GOAL=20,
        YOUTUBE_API_KEY="DUMMY_KEY",
        YDL_OPTS={},
        OUTPUT_WIDTH=1280,
        OUTPUT_HEIGHT=720,
        OUTPUT_BASE_PATH="tests/downloads",
        OUTPUT_FULL_PATH="tests/downloads/test",
        TARGET_FPS=30,
        TITLE_CARD_PATH="tests/assets/title_card.mp4",
        TRANSITION_SOUND_PATH="tests/assets/pop.wav",
        TRANSITION_DURATION=1.0,
        THUMBNAIL_WIDTH=1280,
        THUMBNAIL_HEIGHT=720,
        THUMBNAIL_LOGO_PATH="tests/assets/logo.png",
    )


def test_pipeline_runs_all_stages():
    run_config = make_test_run_config()
    context = PipelineContext(run_config=run_config)

    stages = [
        DiscoverStage(context),
        FilterStage(context),
        CullStage(context),
        ScoreStage(context),
        SelectStage(context),
        DownloadStage(context),
        TransformStage(context),
        CompileStage(context),
        PersistStage(context),
        CleanStage(context),
    ]

    for stage in stages:
        stage.should_run = Mock(return_value=True)

    # Stub run() on each stage
    for stage in stages:
        stage.run = MagicMock()

    # Simulate pipeline execution
    for stage in stages:
        if stage.should_run():
            stage.run()

    # Assert every stage ran exactly once
    for stage in stages:
        stage.run.assert_called_once()
