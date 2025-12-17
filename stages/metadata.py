from .base import Stage


class MetadataStage(Stage):
    @property
    def name(self):
        return "Generate Metadata"

    def should_run(self):
        # e.g., skip if title/description already exist
        return True

    def run(self):
        # logic to create title, description, etc.
        pass
