from .base import Stage


class TransformStage(Stage):
    @property
    def name(self):
        return "Transform Clips"

    def should_run(self):
        # e.g., skip if clips are already normalized
        return True

    def run(self):
        # logic to apply transformations to clips
        pass
