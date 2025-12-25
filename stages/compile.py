import os
from pathlib import Path

from moviepy import (
    AudioFileClip,
    ColorClip,
    VideoFileClip,
    vfx,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips,
)
from tqdm import tqdm

from domain.clip import ClipState
from domain.pipeline_context import PipelineContext
from domain.stage import Stage
from utils.compile_utils import get_outro_clip


class CompileStage(Stage):
    INPUT_CLIP_STATE = ClipState.TRANSFORMED
    OUTPUT_CLIP_STATE = ClipState.COMPILED

    @property
    def name(self):
        return "<COMPILE>"

    def should_run(self, ctx: PipelineContext) -> bool:
        if (
            ctx.clip.count_clips_in_state(ClipState.ELIGIBLE)
            >= ctx.run_config.TARGET_COUNT
        ):
            return True
        else:
            return False

    def run(self, ctx: PipelineContext) -> None:
        keyword = ctx.run_config.KEYWORD
        output_path = os.path.join(
            ctx.run_config.OUTPUT_FULL_PATH, f"{keyword}_compilation.mp4"
        )
        transition_sound_path = ctx.run_config.TRANSITION_SOUND_PATH
        title_card_path = ctx.run_config.TITLE_CARD_PATH
        output_width = ctx.run_config.OUTPUT_WIDTH
        output_height = ctx.run_config.OUTPUT_HEIGHT
        transition_duration = ctx.run_config.TRANSITION_DURATION
        target_fps = ctx.run_config.TARGET_FPS

        # Sort videos by view count ascending
        ctx.clip.clips_in_state(ClipState.DOWNLOADED).sort(key=lambda v: v.metadata.view_count)

        if not Path(transition_sound_path).exists():
            raise Exception(
                f"⚠ No transition audio found at  at {ctx.run_config.TRANSITION_SOUND_PATH}"
            )

        transition_sound_clip = AudioFileClip(transition_sound_path).subclipped(
            0, transition_duration
        )

        transition_clip = ColorClip(
            size=(output_width, output_height), color=(0, 0, 0), duration=transition_duration
        )
        transition_clip = transition_clip.with_audio(transition_sound_clip)

        output_clips = []
        # --- Title Card ---
        if os.path.exists(title_card_path):
            title_clip = VideoFileClip(title_card_path)
            title_clip = title_clip.with_effects([vfx.Resize((output_width, output_height))])
            output_clips.append(title_clip)
        else:
            print(f"⚠ No title card found at {title_card_path}")
            return

        num_clips = len(ctx.clip.clips)
        downloaded = ctx.clip.clips_in_state(ClipState.TRANSFORMED)
        for idx, clip in enumerate(tqdm(downloaded, "Compiling clips")):
            print(clip)
            if not clip.is_stage_ready(self.INPUT_CLIP_STATE):
                continue
            try:
                index = num_clips - idx
                # centered bold text
                text_clip = TextClip(
                    text="#" + str(index),
                    font_size=int(output_height * 0.28),  # scales automatically
                    size=(output_width, output_height),
                    color="#4C7EFF",
                    font="Impact",
                    horizontal_align="center",
                    vertical_align="center",
                    duration=transition_duration,
                )

                # combine layers
                transition_clip = CompositeVideoClip([transition_clip, text_clip])

                output_clips.append(transition_clip)
                content_clip = VideoFileClip(clip.processed_path)
                output_clips.append(content_clip)
                clip.state = self.OUTPUT_CLIP_STATE

            except Exception as e:
                print(f"⚠ Failed to compile {str(clip)}: error{str(e)}")

        output_clips.append(get_outro_clip())
        title_clip = VideoFileClip(title_card_path)
        title_clip = title_clip.with_effects([vfx.Resize((output_width, output_height))])
        output_clips.append(title_clip)

        # --- Concatenate all clips ---
        output_video = concatenate_videoclips(
            output_clips,
            method="compose",
        )
        output_video.write_videofile(
            output_path,
            fps=target_fps,
            codec="libx264",
            audio_codec="aac",
            bitrate="8000k",
            threads=4,
        )

        for clip in output_clips:
            clip.close()
        output_video.close()
