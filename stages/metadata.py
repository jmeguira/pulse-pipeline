import os

from domain.stage import Stage
from utils.metadata_utils import get_compilation_title, get_compilation_description


class MetadataStage(Stage):
    @property
    def name(self):
        return "Generate Metadata"

    def should_run(self):
        # e.g., skip if title/description already exist
        return True

    def run(self):
        run_config = self.context.run_config
        output_path = self.context.run_config.OUTPUT_FULL_PATH
        clips = self.context.clips

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
