
import asyncio
import json
import logging
import os
import re
import time

from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

from pipeline.prompts import (
    build_combined_messages,
    build_narrative_messages,
)

logger = logging.getLogger("narrate-ai.pipeline")

_model: ModelInference | None = None
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
                model_id="ibm/granite-4-h-small",
                credentials=credentials,
                space_id=os.environ["WATSONX_SPACE_ID"],
                params={
                    GenParams.DECODING_METHOD: "greedy",
                    GenParams.MAX_NEW_TOKENS: 1500,
                    GenParams.REPETITION_PENALTY: 1.1,
                },
            )
        except Exception:
            _model = None
            raise
    return _model


def _sanitise_data(obj: object) -> object:
    if isinstance(obj, str):
        return obj[:_MAX_STR_LEN] + ("…" if len(obj) > _MAX_STR_LEN else "")
    if isinstance(obj, dict):
        return {
            (k[:_MAX_STR_LEN] if isinstance(k, str) else k): _sanitise_data(v)
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_sanitise_data(item) for item in obj]
    return obj


def _sanitise_dict(data: dict) -> dict:
    result = _sanitise_data(data)
    return result if isinstance(result, dict) else {}


def _chat(model: ModelInference, messages: list[dict]) -> str:
    for attempt in range(3):
        try:
            response = model.chat(messages=messages)
            choices = response.get("choices", [])
            if not choices:
                raise ValueError(f"Watsonx returned no choices. Full response: {response}")
            return choices[0]["message"]["content"].strip()
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                wait = 30 * (attempt + 1)
                logger.warning("Rate limited, waiting %ds (attempt %d/3)", wait, attempt + 1)
                time.sleep(wait)
            else:
                raise


async def _chat_async(model: ModelInference, messages: list[dict]) -> str:
    return await asyncio.get_running_loop().run_in_executor(None, _chat, model, messages)


def _parse_json(raw: str) -> dict | list:
    match = re.search(r"[\[{]", raw)
    if not match:
        raise ValueError(f"Model output contained no JSON.\nRaw output was:\n{raw[:500]}")
    candidate = raw[match.start():]
    candidate = re.sub(r"\s*```\s*$", "", candidate.strip())
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model returned invalid JSON: {exc}\nRaw output was:\n{raw[:500]}") from exc


def _extract_headline(narrative: str) -> tuple[str, str]:
    match = re.search(r"HEADLINE:\s*(.+)", narrative, re.IGNORECASE)
    if match:
        headline = match.group(1).strip()
        body = narrative[match.end():].strip()
        return headline, body
    lines = [line for line in narrative.splitlines() if line.strip()]
    if not lines:
        return "Untitled", narrative.strip()
    return lines[0].strip(), "\n".join(lines[1:]).strip()


async def run_pipeline(
    structured_data: dict,
    audience: str,
    tone: str,
    request_id: str = "-",
) -> dict:
    model = _get_model()
    safe_data = _sanitise_dict(structured_data)

    # ── Step 1: Analyze + Extract insights (combined) ────────────────────
    t0 = time.perf_counter()
    combined_messages = build_combined_messages(safe_data, audience, 5)
    raw_combined = await _chat_async(model, combined_messages)
    logger.info("[%s] step1 combined %.2fs", request_id, time.perf_counter() - t0)

    try:
        combined_parsed = _parse_json(raw_combined)
        insights = combined_parsed.get("insights", []) if isinstance(combined_parsed, dict) else []
    except ValueError as exc:
        logger.warning("[%s] step1 parse failed (%s)", request_id, exc)
        insights = []

    # ── Step 2: Generate narrative ───────────────────────────────────────
    t1 = time.perf_counter()
    narrative_messages = build_narrative_messages(insights, audience, tone)
    raw_narrative = await _chat_async(model, narrative_messages)
    logger.info("[%s] step2 narrative %.2fs", request_id, time.perf_counter() - t1)

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