import os
from pathlib import Path

import yt_dlp
from tqdm import tqdm

from domain.clip import ClipState
from domain.stage import Stage


class DownloadStage(Stage):
    INPUT_CLIP_STATE = ClipState.ELIGIBLE
    OUTPUT_CLIP_STATE = ClipState.DOWNLOADED

    @property
    def name(self):
        return "Download videos"

    def should_run(self):
        return True

    def run(self):
        keyword = self.context.run_config.keyword
        output_path = self.context.run_config.OUTPUT_FULL_PATH
        os.makedirs(output_path, exist_ok=True)
        YDL_OPTS = {
            **self.context.run_config.YDL_OPTS,
            "outtmpl": os.path.join(output_path, "%(id)s.%(ext)s"),
        }

        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            for clip in tqdm(
                [v for v in self.context.clips if v.state == ClipState.ELIGIBLE],
                desc=f"Downloading {self.context.run_config.target_count} videos for '{keyword}'",
                unit="video",
            ):
                if not clip.is_stage_ready(self.INPUT_CLIP_STATE):
                    continue
                try:
                    ydl.download(clip.metadata.url)
                except Exception as e:
                    clip.set_state(ClipState.FAILED)
                    clip.failure_reason = f"❌ Failed to download {str(clip)}\n\nError: {str(e)}"
                    continue

                clip.set_state(ClipState.DOWNLOADED)
                clip.raw_path = Path(output_path) / f"{clip.metadata.id}.mp4"
