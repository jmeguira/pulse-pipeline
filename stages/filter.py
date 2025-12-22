from domain.clip import ClipState
from domain.stage import Stage


class FilterStage(Stage):

    INPUT_CLIP_STATE: ClipState | None = None
    OUTPUT_CLIP_STATE: ClipState | None = None

    def name(self) -> str:
        """Human-readable stage name."""
        pass

    def should_run(self) -> bool:
        """Return True if this stage should execute."""
        return True

    def run(self):
        """Stage-specific behavior."""
        pass
