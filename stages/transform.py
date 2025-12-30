import os
from pathlib import Path

from moviepy import VideoFileClip
from tqdm import tqdm

from domain.clip import ClipState
from domain.pipeline_context import PipelineContext
from domain.stage import Stage, StageGroup
from utils.preprocess_utils import normalize_clip_audio, transform_clip


class TransformStage(Stage):
    INPUT_CLIP_STATE = ClipState.DOWNLOADED
    OUTPUT_CLIP_STATE = ClipState.TRANSFORMED
    STAGE_GROUP = StageGroup.ASSEMBLE

    @property
    def name(self):
        return "<TRANSFORM>"

    def is_stage_enabled(self, ctx: PipelineContext) -> bool:
        # e.g., skip if clips are already normalized
        return True

    def run(self, ctx: PipelineContext) -> None:
        for idx, clip in enumerate(
            tqdm(
                ctx.clip.clips_in_state(state=ClipState.DOWNLOADED),
                desc="Pre-processing clips",
            )
        ):

            if not clip.is_stage_ready(self.INPUT_CLIP_STATE):
                continue

            if clip.processed_path and Path(clip.processed_path).exists():
                continue

            if ctx.run_config.ENABLE_LUFS:
                try:
                    normalize_clip_audio(ctx.run_config, clip.raw_path)
                except Exception as e:
                    clip.set_state(ClipState.FAILED)
                    clip.status_reason = f"{type(e).__name__}: {e}"
                    ctx.error(f"Failed to normalize clip audio: {str(clip.id[:8])}")
                    if ctx.flags.strict:
                        ctx.error(f"{type(e).__name__}: {e}")
                        raise
                    continue

            try:
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
                        logger=None,
                    )
                    clip.processed_path = processed_output_path
                    clip.set_state(self.OUTPUT_CLIP_STATE)

            except Exception as e:
                clip.set_state(ClipState.FAILED)
                clip.status_reason = f"{type(e).__name__}: {e}"
                ctx.error(f"Failed to transform clip: {str(clip.id[:8])}")
                if ctx.flags.strict:
                    ctx.error(f"{type(e).__name__}: {e}")
                    raise
                continue
        pass
