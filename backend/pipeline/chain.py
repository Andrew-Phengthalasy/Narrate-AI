import asyncio
import json
import logging
import os
import re
import time

from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

try:
    from .prompts import (                        # package import (local dev)
        build_summarize_messages,
        build_insight_messages,
        build_narrative_messages,
    )
except ImportError:
    from prompts import (                         # flat import (Vercel)
        build_summarize_messages,
        build_insight_messages,
        build_narrative_messages,
    )

logger = logging.getLogger("narrate-ai.pipeline")

# Module-level cache — one connection per process lifetime (avoids reconnecting
# on every request, which is especially costly on Vercel cold starts).
_model: ModelInference | None = None

# Maximum length of any single string value embedded in the prompt (chars).
# Prevents oversized cell values from flooding the context window.
_MAX_STR_LEN = 300


def _get_model() -> ModelInference:
    global _model
    if _model is None:
        credentials = Credentials(
            url=os.environ["WATSONX_URL"],
            api_key=os.environ["WATSONX_API_KEY"],
        )
        try:
            _model = ModelInference(
                model_id="ibm/granite-13b-instruct-v2",
                credentials=credentials,
                project_id=os.environ["WATSONX_PROJECT_ID"],
                params={
                    # greedy decoding — TEMPERATURE is incompatible and must be omitted
                    GenParams.DECODING_METHOD: "greedy",
                    GenParams.MAX_NEW_TOKENS: 1500,
                    GenParams.REPETITION_PENALTY: 1.1,
                },
            )
        except Exception:
            _model = None  # don't cache a failed initialisation
            raise
    return _model


def _sanitise_data(obj: object) -> object:  # type: ignore[return]
    """Recursively truncate long strings in structured_data before embedding in prompts.

    This limits prompt-injection surface: a CSV cell containing 'Ignore all
    previous instructions' is truncated to _MAX_STR_LEN chars.
    """
    if isinstance(obj, str):
        return obj[:_MAX_STR_LEN] + ("…" if len(obj) > _MAX_STR_LEN else "")
    if isinstance(obj, dict):
        # Truncate both keys and values — a long key is unlikely but still a
        # potential injection vector if user-supplied column names are embedded.
        return {
            (k[:_MAX_STR_LEN] if isinstance(k, str) else k): _sanitise_data(v)
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_sanitise_data(item) for item in obj]
    return obj


def _sanitise_dict(data: dict) -> dict:
    """Wrapper that guarantees a dict return type for type-checked call sites."""
    result = _sanitise_data(data)
    return result if isinstance(result, dict) else {}


def _chat(model: ModelInference, messages: list[dict]) -> str:
    """Send a chat-style messages list and return the assistant text."""
    response = model.chat(messages=messages)
    choices = response.get("choices", [])
    if not choices:
        raise ValueError(
            f"Watsonx returned no choices (possible content filter or timeout). "
            f"Full response: {response}"
        )
    return choices[0]["message"]["content"].strip()


async def _chat_async(model: ModelInference, messages: list[dict]) -> str:
    """Run the blocking _chat call in a thread so the event loop stays free."""
    return await asyncio.get_running_loop().run_in_executor(None, _chat, model, messages)


def _parse_json(raw: str) -> dict | list:
    """Extract and parse the first JSON object or array from the model output.

    Handles three common model response patterns:
    - Clean JSON with no wrapper text
    - JSON wrapped in ```json ... ``` fences
    - JSON preceded by any preamble text (e.g. "Here is the output:\\n{...}")

    Raises ValueError with the raw output included so failures are debuggable.
    """
    match = re.search(r"[\[{]", raw)
    if not match:
        raise ValueError(
            f"Model output contained no JSON object or array.\nRaw output was:\n{raw[:500]}"
        )
    candidate = raw[match.start():]
    candidate = re.sub(r"\s*```\s*$", "", candidate.strip())
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Model returned invalid JSON: {exc}\nRaw output was:\n{raw[:500]}"
        ) from exc


def _extract_headline(narrative: str) -> tuple[str, str]:
    """Split 'HEADLINE: ...\n rest of article' into (headline, body)."""
    match = re.search(r"HEADLINE:\s*(.+)", narrative, re.IGNORECASE)
    if match:
        headline = match.group(1).strip()
        body = narrative[match.end():].strip()
        return headline, body
    # Fallback: treat first non-empty line as headline
    lines = [line for line in narrative.splitlines() if line.strip()]
    if not lines:
        return "Untitled", narrative.strip()
    return lines[0].strip(), "\n".join(lines[1:]).strip()


def _n_insights_from_summary(data_summary: dict) -> int:
    """Derive insight count from Step 1 output: 3 for ≤3 key metrics, 5 for richer."""
    key_metrics = data_summary.get("key_metrics", [])
    return 3 if len(key_metrics) <= 3 else 5


async def run_pipeline(
    structured_data: dict,
    audience: str,
    tone: str,
    request_id: str = "-",
) -> dict:
    """Execute the 3-step Narrate-AI pipeline asynchronously and return the full result."""
    model = _get_model()
    safe_data = _sanitise_dict(structured_data)

    # ── Step 1: Summarize ────────────────────────────────────────────────
    t0 = time.perf_counter()
    summarize_messages = build_summarize_messages(safe_data)
    raw_summary = await _chat_async(model, summarize_messages)
    logger.info("[%s] step1 summarize %.2fs", request_id, time.perf_counter() - t0)

    raw_summary_parsed = _parse_json(raw_summary)
    data_summary: dict = raw_summary_parsed if isinstance(raw_summary_parsed, dict) else {}

    # ── Step 2: Extract insights ─────────────────────────────────────────
    t1 = time.perf_counter()
    n = _n_insights_from_summary(data_summary)
    insight_messages = build_insight_messages(data_summary, audience, n)
    raw_insights = await _chat_async(model, insight_messages)
    logger.info("[%s] step2 insights %.2fs", request_id, time.perf_counter() - t1)

    try:
        raw_insights_parsed = _parse_json(raw_insights)
        if not isinstance(raw_insights_parsed, list):
            raise ValueError("Insights response was not a JSON array")
        insights: list[dict] = raw_insights_parsed
    except ValueError as exc:
        logger.warning("[%s] step2 parse failed (%s) — using empty insights", request_id, exc)
        insights = []

    # ── Step 3: Generate narrative ───────────────────────────────────────
    t2 = time.perf_counter()
    narrative_messages = build_narrative_messages(insights, audience, tone)
    raw_narrative = await _chat_async(model, narrative_messages)
    logger.info("[%s] step3 narrative %.2fs", request_id, time.perf_counter() - t2)

    headline, body = _extract_headline(raw_narrative)

    logger.info(
        "[%s] pipeline total %.2fs insights=%d words=%d",
        request_id, time.perf_counter() - t0, len(insights), len(body.split()),
    )

    return {
        "headline": headline,
        "narrative": body,
        "insights": insights,
        "word_count": len(body.split()),
    }
