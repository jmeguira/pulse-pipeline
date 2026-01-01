import json
import random
import time

from googleapiclient.errors import HttpError
from googleapiclient.http import HttpRequest

from domain.keyword_config import KeywordConfig
from domain.pipeline_context import PipelineContext

RETRY_STATUSES = {429, 500, 503}
RETRYABLE_403_REASONS = {"rateLimitExceeded", "userRateLimitExceeded", "quotaExceeded"}


def build_query(keyword_config: KeywordConfig) -> str:
    include = " ".join(keyword_config.query_include)
    exclude = " ".join(f"-{term}" for term in keyword_config.query_exclude)
    return f"{include} {exclude}".strip()


def extract_status_code(e: HttpError) -> int | None:
    if hasattr(e, "resp") and hasattr(e.resp, "status"):
        return e.resp.status
    return getattr(e, "status_code", None)


def extract_reasons(e: HttpError) -> list[str]:
    try:
        raw = e.content.decode("utf-8", errors="replace")
        data = json.loads(raw)
        errs = data.get("error", {}).get("errors", [])
        return [err.get("reason") for err in errs if isinstance(err, dict) and err.get("reason")]
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, KeyError):
        return []


def extract_retry_after(e: HttpError) -> int | None:
    resp = getattr(e, "resp", None)
    if not resp:
        return None
    retry_after = resp.get("retry-after") or resp.get("Retry-After")
    if not retry_after:
        return None
    try:
        return int(retry_after)
    except ValueError:
        return None


def youtube_execute(ctx: PipelineContext, req: HttpRequest) -> dict:
    max_attempts = ctx.run_config.YOUTUBE_API_MAX_ATTEMPTS
    base_delay = ctx.run_config.YOUTUBE_API_BASE_DELAY_S
    max_delay = ctx.run_config.YOUTUBE_API_MAX_DELAY_S
    jitter_pct = ctx.run_config.YOUTUBE_API_JITTER_PCT

    for attempt in range(1, max_attempts + 1):
        try:
            return req.execute()
        except HttpError as e:
            status_code = extract_status_code(e)
            reasons = extract_reasons(e)

            if status_code is None:
                ctx.error(f"youtube.give_up.no_status_code | attempt={attempt} | reasons={reasons}")
                raise

            retry_after = extract_retry_after(e)

            retryable_status = status_code in RETRY_STATUSES
            matched_reason = next((r for r in reasons if r in RETRYABLE_403_REASONS), None)
            retryable_403 = status_code == 403 and matched_reason is not None
            retryable = retryable_status or retryable_403

            if not retryable:
                ctx.error(
                    "youtube.give_up.not_retryable | "
                    f"attempt={attempt} | "
                    f"status={status_code} | "
                    f"reasons={reasons} | "
                    f"retryable_status={retryable_status} | "
                    f"matched_403_reason={matched_reason}"
                )
                raise

            if attempt == max_attempts:
                ctx.error(
                    f"youtube.give_up.max_attempts | attempt={attempt} | status={status_code} | reasons={reasons}"
                )
                raise

            delay = (
                retry_after
                if retry_after is not None
                else min(max_delay, base_delay * (2 ** (attempt - 1)))
            )
            delay += random.uniform(0, jitter_pct * delay)
            ctx.debug(
                "youtube.retry | "
                f"attempt={attempt}/{max_attempts} | "
                f"status={status_code} | "
                f"reason={matched_reason} | "
                f"delay={delay:.2f}s | "
                f"retry_after={retry_after}"
            )
            time.sleep(delay)

    raise RuntimeError("unreachable: youtube_execute exited retry loop")
