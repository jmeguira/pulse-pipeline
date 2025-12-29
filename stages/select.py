import json
from datetime import datetime
from pathlib import Path

from domain.clip import ClipState
from domain.pipeline_context import PipelineContext
from domain.stage import Stage, StageGroup


def write_clips_json(ctx: PipelineContext, state: ClipState = None) -> None:
    clips = ctx.clip.clips_in_state(state) if state else ctx.clip.clips

    payload = {
        "generated_at": datetime.now().isoformat(),
        "clip_count": len(clips),
        "count_by_state": ctx.clip.count_clips_by_state(),
        "clips": [c.to_dict() for c in clips],
    }

    out_path = Path(ctx.run_config.OUTPUT_FULL_PATH) / "clips.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4)


class SelectStage(Stage):

    INPUT_CLIP_STATE = ClipState.ELIGIBLE
    OUTPUT_CLIP_STATE = ClipState.SELECTED
    STAGE_GROUP = StageGroup.DISCOVER

    def name(self) -> str:
        return "<SELECT>"

    def is_stage_enabled(self, ctx: PipelineContext) -> bool:
        return True

    def run(self, ctx: PipelineContext) -> None:
        eligible = sorted(
            ctx.clip.clips_in_state(ClipState.ELIGIBLE),
            key=lambda c: c.metadata.view_count or 0,
            reverse=True,
        )

        for clip in eligible[:ctx.run_config.TARGET_COUNT]:
            clip.state = ClipState.SELECTED

        try:
            write_clips_json(ctx, ClipState.SELECTED)
        except Exception as e:
            ctx.error(f"Failed to write clips.json file. Error: {e}")
            raise
