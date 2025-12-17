from .base import Stage


class CleanStage(Stage):
    @property
    def name(self):
        return "Clean artifacts. Metadata consolidation. Run logging."

    def should_run(self):
        # e.g., skip if compilation already exists
        return True

    def run(self):
        # logic to create final compilation
        pass
