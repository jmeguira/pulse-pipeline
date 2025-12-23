import os
from pathlib import Path

from moviepy import VideoFileClip
from tqdm import tqdm

from domain.clip import ClipState
from domain.pipeline_context import PipelineContext
from domain.stage import Stage
from utils.preprocess_utils import normalize_clip_audio, transform_clip


class TransformStage(Stage):
    INPUT_CLIP_STATE = ClipState.DOWNLOADED
    OUTPUT_CLIP_STATE = ClipState.TRANSFORMED

    @property
    def name(self):
        return "Transform Clips"

    def should_run(self, ctx: PipelineContext) -> bool:
        # e.g., skip if clips are already normalized
        return True

    def run(self, ctx: PipelineContext) -> None:
        for idx, clip in enumerate(
            tqdm(
                ctx.clip.clips,
                desc="Pre-processing clips",
            )
        ):
            try:
                if not clip.is_stage_ready(self.INPUT_CLIP_STATE):
                    continue

                if clip.processed_path and Path(clip.processed_path).exists():
                    continue

                if ctx.run_config.ENABLE_LUFS:
                    try:
                        normalize_clip_audio(ctx.run_config, clip.raw_path)
                    except Exception as e:
                        print(f"⚠ Failed to normalize {str(clip)}\n\nError: {str(e)}")

                        continue

                with VideoFileClip(clip.raw_path).resized(
                    height=ctx.run_config.OUTPUT_HEIGHT
                ) as processed_clip:
                    processed_clip = transform_clip(processed_clip)
                    processed_output_path = os.path.join(
                        ctx.run_config.OUTPUT_FULL_PATH,
                        f"{clip.metadata.id}_processed.mp4",
                    )
                    processed_clip.write_videofile(
                        str(processed_output_path),
                        fps=ctx.run_config.TARGET_FPS,
                        codec="libx264",
                        audio_codec="aac",
                        verbose=False,
                        logger=None,
                    )
                    clip.processed_path = processed_output_path
                    clip.set_state(ClipState.PROCESSED)

            except Exception as e:
                clip.set_state(ClipState.FAILED)
                clip.failure_reason = f"❌ Failed to pre-process {str(clip)}\n\nError: {str(e)}"
        pass
