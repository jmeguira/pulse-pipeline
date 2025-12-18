from moviepy import VideoFileClip
from tqdm import tqdm

from types.clip import ClipState
from types.stage import Stage
from utils.preprocess_utils import normalize_clip_audio, transform_clip


class PreprocessStage(Stage):
    INPUT_CLIP_STATE = ClipState.DOWNLOADED
    OUTPUT_CLIP_STATE = ClipState.PROCESSED

    @property
    def name(self):
        return "Transform Clips"

    def should_run(self):
        # e.g., skip if clips are already normalized
        return True

    def run(self):
        for idx, video in enumerate(tqdm(self.context.videos, desc="Pre-processing clips")):
            try:
                if self.context.run_config.enable_lufs:
                    try:
                        normalize_clip_audio(self.context.run_config, video["file_path"])
                    except Exception as e:
                        print(f"⚠ Failed to normalize {video['file_path']}: {e}")

                clip = VideoFileClip(video["file_path"]).resized(
                    height=self.context.run_config.OUTPUT_HEIGHT
                )
                clip = transform_clip(clip)
                self.context.clips.append(clip)

            except Exception as e:
                print(f"⚠ Failed to pre-process {video['file_path']}: {e}")
        pass
