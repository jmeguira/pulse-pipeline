from .base import Stage


class CompileStage(Stage):
    @property
    def name(self):
        return "Compile Video"

    def should_run(self):
        # e.g., skip if compilation already exists
        return True

    def run(self):
        # logic to create final compilation
        pass
