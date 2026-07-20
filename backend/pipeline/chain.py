import json
import os
import re

from ibm_watsonx_ai import APIClient, Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

from .prompts import (
    build_summarize_messages,
    build_insight_messages,
    build_narrative_messages,
)


def _get_model() -> ModelInference:
    credentials = Credentials(
        url=os.environ["WATSONX_URL"],
        api_key=os.environ["WATSONX_API_KEY"],
    )
    client = APIClient(credentials)
    return ModelInference(
        model_id="ibm/granite-13b-instruct-v2",
        credentials=credentials,
        project_id=os.environ["WATSONX_PROJECT_ID"],
        params={
            GenParams.DECODING_METHOD: "greedy",
            GenParams.MAX_NEW_TOKENS: 1500,
            GenParams.TEMPERATURE: 0.7,
            GenParams.REPETITION_PENALTY: 1.1,
        },
    )


def _chat(model: ModelInference, messages: list[dict]) -> str:
    """Send a chat-style messages list and return the assistant text."""
    response = model.chat(messages=messages)
    return response["choices"][0]["message"]["content"].strip()


def _parse_json(raw: str) -> dict | list:
    """Strip markdown fences if present, then parse JSON."""
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"```\s*$", "", cleaned.strip(), flags=re.MULTILINE)
    return json.loads(cleaned)


def _extract_headline(narrative: str) -> tuple[str, str]:
    """Split 'HEADLINE: ...\n rest of article' into (headline, body)."""
    match = re.search(r"HEADLINE:\s*(.+)", narrative, re.IGNORECASE)
    if match:
        headline = match.group(1).strip()
        body = narrative[match.end():].strip()
        return headline, body
    # Fallback: treat first line as headline
    lines = narrative.splitlines()
    return lines[0].strip(), "\n".join(lines[1:]).strip()


def run_pipeline(structured_data: dict, audience: str, tone: str) -> dict:
    """Execute the 3-step Narrate-AI pipeline and return the full result."""
    model = _get_model()

    # ── Step 1: Summarize ────────────────────────────────────────────────
    summarize_messages = build_summarize_messages(structured_data)
    raw_summary = _chat(model, summarize_messages)
    data_summary = _parse_json(raw_summary)

    # ── Step 2: Extract insights ─────────────────────────────────────────
    insight_messages = build_insight_messages(data_summary, audience)
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
