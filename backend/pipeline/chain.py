import json
import os
import re

from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

from .prompts import (
    build_summarize_messages,
    build_insight_messages,
    build_narrative_messages,
    _n_insights,
)

# Module-level cache — one connection per process lifetime (avoids reconnecting
# on every request, which is especially costly on Vercel cold starts).
_model: ModelInference | None = None


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


def _chat(model: ModelInference, messages: list[dict]) -> str:
    """Send a chat-style messages list and return the assistant text."""
    response = model.chat(messages=messages)
    return response["choices"][0]["message"]["content"].strip()


def _parse_json(raw: str) -> dict | list:
    """Extract and parse the first JSON object or array from the model output.

    Handles three common model response patterns:
    - Clean JSON with no wrapper text
    - JSON wrapped in ```json ... ``` fences
    - JSON preceded by any preamble text (e.g. "Here is the output:\\n{...}")

    Raises ValueError with the raw output included so failures are debuggable.
    """
    # Find the first { or [ — skip any preamble the model emitted
    match = re.search(r"[\[{]", raw)
    if not match:
        raise ValueError(
            f"Model output contained no JSON object or array.\nRaw output was:\n{raw[:500]}"
        )
    candidate = raw[match.start():]
    # Strip any trailing markdown fence that may follow the JSON
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
    lines = [l for l in narrative.splitlines() if l.strip()]
    if not lines:
        return "Untitled", narrative.strip()
    return lines[0].strip(), "\n".join(lines[1:]).strip()


def run_pipeline(structured_data: dict, audience: str, tone: str) -> dict:
    """Execute the 3-step Narrate-AI pipeline and return the full result."""
    model = _get_model()

    # ── Step 1: Summarize ────────────────────────────────────────────────
    summarize_messages = build_summarize_messages(structured_data)
    raw_summary = _chat(model, summarize_messages)
    data_summary = _parse_json(raw_summary)

    # ── Step 2: Extract insights ─────────────────────────────────────────
    n = _n_insights(structured_data)
    insight_messages = build_insight_messages(data_summary, audience, n)
    raw_insights = _chat(model, insight_messages)
    insights: list[dict] = _parse_json(raw_insights)

    # ── Step 3: Generate narrative ───────────────────────────────────────
    narrative_messages = build_narrative_messages(insights, audience, tone)
    raw_narrative = _chat(model, narrative_messages)
    headline, body = _extract_headline(raw_narrative)

    return {
        "headline": headline,
        "narrative": body,
        "insights": insights,
        "word_count": len(body.split()),
    }
