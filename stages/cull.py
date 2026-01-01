from domain.clip import ClipState
from domain.pipeline_context import PipelineContext
from domain.stage import Stage, StageGroup


def is_english(s: str) -> bool:
    return s.lower().replace("_", "-").startswith("en")


class CullStage(Stage):
    INPUT_CLIP_STATE = ClipState.ELIGIBLE
    OUTPUT_CLIP_STATE = ClipState.FILTERED
    STAGE_GROUP = StageGroup.DISCOVER

    @property
    def name(self) -> str:
        return "<CULL>"

    def is_stage_enabled(self, ctx: PipelineContext) -> bool:
        return True

    def run(self, ctx: PipelineContext) -> None:
        # TEMP: Sorting by view_count and truncating to target_count for testing
        eligible_clips = ctx.clip.clips_in_state(ClipState.ELIGIBLE)
        eligible_count = len(eligible_clips)
        candidates_needed = ctx.run_config.CANDIDATE_GOAL - eligible_count
        if candidates_needed <= 0:
            return

        cull_non_english = ctx.run_config.CULL_NON_ENGLISH_CONTENT

        for clip in eligible_clips:
            lang = clip.metadata.default_language
            if cull_non_english and lang and not is_english(lang):
                clip.state = ClipState.CULLED
                clip.status_reason = f"non_english_default_language: {lang}"
                continue

            audio_lang = clip.metadata.default_audio_language
            if cull_non_english and audio_lang and not is_english(audio_lang):
                clip.state = ClipState.CULLED
                clip.status_reason = f"non_english_audio_language: {audio_lang}"
                continue
