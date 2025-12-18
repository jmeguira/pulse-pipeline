# tests/pipeline_test.py
from datetime import date
from unittest.mock import MagicMock

from stages.compile import CompileStage
from stages.download import DownloadStage
from stages.fetch import FetchStage
from stages.metadata import MetadataStage
from stages.preprocess import PreprocessStage
from types.pipeline_context import PipelineContext
from types.run_config import RunConfig


def make_test_run_config():
    return RunConfig(
        keyword="test",
        keyword_config={},  # can be empty dict for test
        target_count=1,
        published_after=date.today(),
        published_before=date.today(),
        enable_lufs=False,
        target_lufs=-14.0,
        batch_size=1,
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
        FetchStage(context),
        DownloadStage(context),
        PreprocessStage(context),
        CompileStage(context),
        MetadataStage(context),
    ]

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
