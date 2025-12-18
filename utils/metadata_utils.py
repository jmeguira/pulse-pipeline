import random

from domain.clip import Clip
from domain.run_config import RunConfig
from utils.utils import get_ordinal


def get_compilation_title(
    run_config: RunConfig,
) -> str:
    """
    Generate Youtube compilation title.

    Example output:
    "😺 Top 20 Cat Shorts Weekly Countdown! (Dec 8th–14th, 2025)"
    """
    start_date = run_config.published_after
    end_date = run_config.published_before
    keyword = run_config.keyword
    target_count = run_config.target_count

    start_day = get_ordinal(start_date.day)
    end_day = get_ordinal(end_date.day)
    start_month = start_date.strftime("%b")
    end_month = end_date.strftime("%b")
    year = end_date.year

    title = (
        f"{random.choice(run_config.keyword_config.title_emojis)} Top {target_count} {keyword.capitalize()} Shorts Weekly Countdown!"
        + f" ({start_month} {start_day}–{end_month} {end_day}, {year})"
    )
    return title


def get_compilation_description(
    run_config: RunConfig,
    clips: list[Clip],
) -> str:
    start_date = run_config.published_after
    end_date = run_config.published_before
    keyword = run_config.keyword
    target_count = run_config.target_count

    generic_emojis = ["🔥", "⭐", "🎬", "😎", "🎉"]
    emoji = random.choice(generic_emojis)

    start_day = get_ordinal(start_date.day)
    end_day = get_ordinal(end_date.day)
    start_month = start_date.strftime("%b")
    end_month = end_date.strftime("%b")
    year = end_date.year

    first_line = (
        f"{emoji} Weekly roundup: the best {keyword} Shorts from #{target_count}→#1!"
        + f" ({start_month} {start_day}–{end_month} {end_day}, {year})"
    )
    cta_line = f"💬 Comment your favorite clip! #{target_count}→#1"
    subscribe_line = "👍 Don't forget to like and subscribe for more!\n"

    disclaimer = (
        "All clips remain property of their original creators. "
        + "This compilation is edited together for entertainment purposes only. "
        + "Please support the original channels!\n"
    )

    # Video list in markdown
    clips_copy = clips[::-1]  # reversed copy
    video_lines = [f"{idx + 1}. {clip.metadata.url}" for idx, clip in enumerate(clips_copy)]
    video_list_text = "🔹 Clips included:\n" + "\n".join(video_lines)

    hashtags = (
        f"\n\n#{keyword} #Shorts #YouTubeShorts #Compilation #BestOf"
        + " #Clips #YouTube #Trending #Viral"
    )

    description = "\n".join(
        [first_line, cta_line, subscribe_line, disclaimer, video_list_text, hashtags]
    )

    return description
