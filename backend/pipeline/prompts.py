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
# Step 1+2 Combined — Data Analyzer + Insight Extractor
# ---------------------------------------------------------------------------
COMBINED_SYSTEM = """\
You are a data analyst and editorial expert. Your job is to analyze a dataset and extract the most compelling insights for a target audience.
Output ONLY a valid JSON object — no prose, no markdown fences, no explanation.
"""

COMBINED_HUMAN = """\
Dataset metadata:
{structured_data}

Target audience: {audience_description}

Produce a JSON object with EXACTLY these keys:
{{
  "topic": "<1-sentence description of what this dataset is about>",
  "key_metrics": ["<metric name>", ...],
  "overall_summary": "<2-3 sentences summarising the dataset>",
  "insights": [
    {{
      "rank": 1,
      "finding": "<1 clear sentence stating the finding>",
      "significance": "<why this matters to the target audience>",
      "data_evidence": "<specific number or comparison that proves this>",
      "emotional_weight": "high|medium|low"
    }}
  ]
}}

Include {n_insights} insights total.
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
    if audience == "social_media":
        return 250
    base = 500
    if tone == "analytical":
        base += 100
    return base


def build_combined_messages(structured_data: dict, audience: str, n_insights: int) -> list[dict]:
    audience_desc = AUDIENCE_DESCRIPTIONS.get(audience, AUDIENCE_DESCRIPTIONS["general_public"])
    return [
        {"role": "system", "content": COMBINED_SYSTEM},
        {"role": "user", "content": COMBINED_HUMAN.format(
            structured_data=json.dumps(structured_data, indent=2),
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