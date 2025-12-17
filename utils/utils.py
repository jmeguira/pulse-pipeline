import re
import string
from datetime import date, timedelta
from typing import Tuple


# Ordinal helper
def get_ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return str(n) + suffix


def keyword_in_title_or_description(
    keyword: str,
    title: str,
    description: str,
) -> bool:
    """
    Returns True if `keyword` or `#keyword` appears as a standalone word
    in either the title or the description.
    """
    keyword = re.escape(keyword.lower())
    text = f"{title} {description}".lower()

    pattern = rf"(?<!\w)(#?{keyword})(?!\w)"
    return re.search(pattern, text) is not None


def clean_title(text: str) -> str:
    """Remove hashtags, emojis, and most punctuation for plain-text description."""
    cleaned = re.sub(r"#\S+", "", text)
    cleaned = re.sub(r"[^\x00-\x7F]", "", cleaned)
    allowed = set(string.ascii_letters + string.digits + " .,")
    cleaned = "".join(c if c in allowed else " " for c in cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def get_date_range_str(start_date: date, end_date: date) -> str:
    """
    Returns a string representation of a date range suitable for folder names,
    e.g. '2025-12-10_2025-12-16'
    """
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    return f"{start_str}_{end_str}"


def get_last_week_date_range() -> Tuple[date, date]:
    target_date = date.today()

    days_since_sunday = (target_date.weekday() + 1) % 7
    most_recent_sunday = target_date - timedelta(days=days_since_sunday)
    previous_monday = most_recent_sunday - timedelta(days=6)

    return previous_monday, most_recent_sunday


def get_last_month_date_range() -> Tuple[date, date]:
    target_date = date.today()

    first_of_this_month = target_date.replace(day=1)
    last_day_prev_month = first_of_this_month - timedelta(days=1)
    first_day_prev_month = last_day_prev_month.replace(day=1)

    return first_day_prev_month, last_day_prev_month


def prompt_keyword_choice(keyword_choices: list[str]) -> str:
    print("Choose a keyword:")
    for i, k in enumerate(keyword_choices, 1):
        print(f"{i}. {k}")
    while True:
        try:
            index = int(input("Enter number: ")) - 1
            if 0 <= index < len(keyword_choices):
                return keyword_choices[index]
        except ValueError:
            pass
        print("Invalid choice, try again.")


def prompt_target_count(default: int = 3) -> int:
    try:
        return int(input(f"Enter target number of clips (default {default}): ") or default)
    except ValueError:
        return default


def prompt_date_range() -> Tuple[date, date]:
    print("Select date range option: [1] last week [2] last month [3] custom")
    option = input("Enter number (default 1): ").strip() or "1"
    if option == "1":
        return get_last_week_date_range()
    elif option == "2":
        return get_last_month_date_range()
    elif option == "3":
        start = date.fromisoformat(input("Start date (YYYY-MM-DD): "))
        end = date.fromisoformat(input("End date (YYYY-MM-DD): "))
        return start, end
    else:
        print("Invalid option, defaulting to last week")
        return get_last_week_date_range()
