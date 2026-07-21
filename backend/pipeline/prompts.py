import json

# ---------------------------------------------------------------------------
# Audience descriptions — injected into insight + narrative prompts
# ---------------------------------------------------------------------------
AUDIENCE_DESCRIPTIONS = {
    "executive": (
        "C-suite executives and senior decision-makers who need concise, "
        "high-impact takeaways with a focus on business implications, risks, and opportunities."
    ),
    "general_public": (
        "General readers with no specialist background. Prioritize human impact, "
        "relatable analogies, and clear explanations of what the numbers mean in everyday life."
    ),
    "academic": (
        "Researchers and academics who expect methodological rigour, precise language, "
        "citation of specific data points, and nuanced discussion of limitations."
    ),
    "social_media": (
        "Social media audiences with short attention spans. Lead with the most surprising "
        "finding, use punchy sentences, and build to a shareable conclusion."
    ),
}

TONE_DESCRIPTIONS = {
    "analytical": "precise, data-driven, measured, and objective — let the numbers speak",
    "storytelling": "narrative-driven, with a clear arc, tension, and resolution — make the data come alive",
    "conversational": "warm, accessible, and direct — as if explaining to a curious friend",
}

# ---------------------------------------------------------------------------
# Step 1 — Data Summarizer
# ---------------------------------------------------------------------------
SUMMARIZE_SYSTEM = """\
You are a data analyst. Your sole job is to extract structure from the provided dataset metadata.
Output ONLY a valid JSON object — no prose, no markdown fences, no explanation.
"""

SUMMARIZE_HUMAN = """\
Dataset metadata:
{structured_data}

Produce a JSON object with EXACTLY these keys:
{{
  "topic": "<1-sentence description of what this dataset is about>",
  "data_shape": "<concise description of dataset dimensions, e.g. '120 rows × 8 columns, 5 numeric and 3 categorical'>",
  "key_metrics": ["<metric name>", ...],
  "anomalies": [
    {{"metric": "<name>", "description": "<what is unusual>", "value": "<specific number>"}},
    ...
  ],
  "trends": [
    {{"metric": "<name>", "direction": "increasing|decreasing|stable", "description": "<1-sentence>"}},
    ...
  ],
  "overall_summary": "<2-3 sentences summarising the dataset at a high level>"
}}
"""

# ---------------------------------------------------------------------------
# Step 2 — Insight Extractor
# ---------------------------------------------------------------------------
INSIGHT_SYSTEM = """\
You are an editorial analyst. Given a structured data summary and a target audience,
identify the most compelling and newsworthy insights.
Output ONLY a valid JSON array — no prose, no markdown fences.
"""

INSIGHT_HUMAN = """\
Data summary:
{data_summary}

Target audience: {audience_description}

Identify the {n_insights} most important insights for this audience. For each insight produce:
{{
  "rank": <1-{n_insights}>,
  "finding": "<1 clear sentence stating the finding>",
  "significance": "<why this matters to the target audience>",
  "data_evidence": "<specific number, percentage, or comparison that proves this>",
  "emotional_weight": "high|medium|low"
}}

Return a JSON array of {n_insights} such objects.
"""

# ---------------------------------------------------------------------------
# Step 3 — Narrative Generator
# ---------------------------------------------------------------------------
NARRATIVE_SYSTEM = """\
You are an award-winning data journalist. You write compelling, accurate narratives
that weave data into prose naturally — never as bullet lists.
"""

NARRATIVE_HUMAN = """\
You are writing for: {audience_description}
Tone: {tone_description}

You have been given a pre-analysed brief of key insights. Write a {word_count}-word article.

Structure:
1. HEADLINE — punchy, specific, newsworthy (no generic titles)
2. LEDE — hook the reader in 2-3 sentences using the highest-impact finding
3. BODY — 3 paragraphs, each building on the previous, weaving in data evidence naturally
4. CLOSING — 1 paragraph with a forward-looking or reflective insight

Rules:
- Never list data as bullets inside the article text
- Every claim must be supported by a specific number from the brief
- The headline must appear on its own line starting with "HEADLINE:"
- Do not add any commentary outside the article

Brief (insights):
{insights}
"""


def _target_word_count(audience: str, tone: str) -> int:
    """Return the target word count based on audience and tone.

    social_media always stays short regardless of tone.
    analytical tone adds 100 words for all other audiences.
    """
    if audience == "social_media":
        return 250
    base = 500
    if tone == "analytical":
        base += 100
    return base


def build_summarize_messages(structured_data: dict) -> list[dict]:
    return [
        {"role": "system", "content": SUMMARIZE_SYSTEM},
        {"role": "user", "content": SUMMARIZE_HUMAN.format(
            structured_data=json.dumps(structured_data, indent=2)
        )},
    ]


def build_insight_messages(data_summary: dict, audience: str, n_insights: int) -> list[dict]:
    audience_desc = AUDIENCE_DESCRIPTIONS.get(audience, AUDIENCE_DESCRIPTIONS["general_public"])
    return [
        {"role": "system", "content": INSIGHT_SYSTEM},
        {"role": "user", "content": INSIGHT_HUMAN.format(
            data_summary=json.dumps(data_summary, indent=2),
            audience_description=audience_desc,
            n_insights=n_insights,
        )},
    ]


def build_narrative_messages(insights: list[dict], audience: str, tone: str) -> list[dict]:
    audience_desc = AUDIENCE_DESCRIPTIONS.get(audience, AUDIENCE_DESCRIPTIONS["general_public"])
    tone_desc = TONE_DESCRIPTIONS.get(tone, TONE_DESCRIPTIONS["storytelling"])
    word_count = _target_word_count(audience, tone)
    return [
        {"role": "system", "content": NARRATIVE_SYSTEM},
        {"role": "user", "content": NARRATIVE_HUMAN.format(
            audience_description=audience_desc,
            tone_description=tone_desc,
            word_count=word_count,
            insights=json.dumps(insights, indent=2),
        )},
    ]
