import os
from pathlib import Path

import yt_dlp
from tqdm import tqdm

from domain.clip import ClipState
from domain.pipeline_context import PipelineContext
from domain.stage import Stage, StageGroup


class DownloadStage(Stage):
    INPUT_CLIP_STATE = ClipState.SELECTED
    OUTPUT_CLIP_STATE = ClipState.DOWNLOADED
    STAGE_GROUP = StageGroup.ASSEMBLE

    @property
    def name(self):
        return "<DOWNLOAD>"

    def is_stage_enabled(self, ctx: PipelineContext) -> bool:
        return True

    def run(self, ctx: PipelineContext):
        keyword = ctx.run_config.KEYWORD
        output_path = ctx.run_config.OUTPUT_FULL_PATH
        os.makedirs(output_path, exist_ok=True)
        ydl_opts = {
            **ctx.run_config.YDL_OPTS,
            "outtmpl": os.path.join(output_path, "%(id)s.%(ext)s"),
        }

        with (yt_dlp.YoutubeDL(ydl_opts) as ydl):
            for clip in tqdm(
                ctx.clip.clips_in_state(ClipState.SELECTED),
                desc=f"Downloading {ctx.run_config.TARGET_COUNT} videos for '{keyword}'",
                unit="video",
            ):
                if not clip.is_stage_ready(self.INPUT_CLIP_STATE):
                    continue
                try:
                    ydl.download(clip.metadata.url)
                except Exception as e:
                    clip.set_state(ClipState.FAILED)
                    clip.status_reason = f"{type(e).__name__}: {e}"
                    ctx.error(f"Failed to download clip: {str(clip.id[:8])}")
                    if ctx.flags.strict:
                        ctx.error(f"{type(e).__name__}: {e}")
                        raise
                    continue

                clip.set_state(ClipState.DOWNLOADED)
                clip.raw_path = Path(output_path) / f"{clip.metadata.id}.mp4"
