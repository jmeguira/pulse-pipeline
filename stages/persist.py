import os

from domain.clip import ClipState
from domain.pipeline_context import PipelineContext
from domain.stage import Stage
from utils.metadata_utils import get_compilation_title, get_compilation_description


class PersistStage(Stage):
    INPUT_CLIP_STATE = ClipState.COMPILED
    OUTPUT_CLIP_STATE = ClipState.PERSISTED

    @property
    def name(self):
        return "<PERSIST>"

    def should_run(self, ctx: PipelineContext) -> bool:
        # e.g., skip if title/description already exist
        return True

    def run(self, ctx: PipelineContext) -> None:
        run_config = ctx.run_config
        output_path = ctx.run_config.OUTPUT_FULL_PATH
        clips = ctx.clip.clips

        # --- Generate title & description ---
        title = get_compilation_title(
            run_config=run_config,
        )

        description = get_compilation_description(
            run_config=run_config,
            clips=clips,
        )

        # Write to files in the same folder as the compilation video
        with open(os.path.join(output_path, "title.txt"), "w", encoding="utf-8") as f:
            f.write(title)

        with open(os.path.join(output_path, "description.txt"), "w", encoding="utf-8") as f:
            f.write(description)

        print(f"✅ Title & description saved in: {output_path}")
