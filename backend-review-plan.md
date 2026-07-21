# Backend Review Plan

## Overview

A folder-by-folder correctness pass followed by prompt quality improvements across the Narrate-AI backend. Work is split into four focused sub-tasks: entry point (`main.py`), parsers, pipeline logic, and prompts. Each sub-task is self-contained and reviewable before moving to the next.

---

## Sub-Task 1 — `main.py` correctness

**Intent**
Fix the one structural issue in the entry point and add a health endpoint so Vercel cold-starts and uptime monitors have something to ping.

**Expected Outcomes**
- A `GET /api/health` endpoint exists and returns `{"status": "ok"}`
- No other logic changes to the entry point

**Todo List**
- [ ] Add `GET /api/health` route returning `{"status": "ok"}`

**Relevant Context**
- [`backend/main.py`](backend/main.py)

**Status** — `[x] done`

---

## Sub-Task 2 — `parsers/` correctness

**Intent**
Fix three concrete bugs across the three parsers.

**Expected Outcomes**
- `csv_parser.py`: `_detect_date_columns` no longer mis-classifies non-date string columns as dates (the `pd.to_datetime` coerce with no threshold check on short strings)
- `pdf_parser.py`: `page_count` reflects total pages in the PDF, not just pages that contained text
- `text_parser.py`: variable `l` renamed to `line` (avoids shadowing built-in `l`/`1` ambiguity, minor style)

**Todo List**
- [ ] `csv_parser.py` — add a minimum row threshold (e.g. at least 3 non-null values) before accepting a column as a date column, to avoid false positives on short string columns
- [ ] `pdf_parser.py` — track total page count from `len(pdf.pages)` separately from `len(text_pages)`, return both as `page_count` and `text_page_count`
- [ ] `text_parser.py` — rename `l` → `line` in the list comprehension

**Relevant Context**
- [`backend/parsers/csv_parser.py`](backend/parsers/csv_parser.py)
- [`backend/parsers/pdf_parser.py`](backend/parsers/pdf_parser.py)
- [`backend/parsers/text_parser.py`](backend/parsers/text_parser.py)

**Status** — `[x] done`

---

## Sub-Task 3 — `pipeline/` correctness

**Intent**
Fix three bugs in the pipeline: the dead `APIClient` call, the unhandled `JSONDecodeError` from model responses, and the NaN-unsafe trend calculation in the preprocessor.

**Expected Outcomes**
- `chain.py`: `APIClient` dead call removed; `_get_model()` cached at module level so only one connection is made per process lifetime
- `chain.py`: `_parse_json` wraps `json.loads` with a clear `ValueError` that includes the raw model output, so pipeline errors are debuggable instead of opaque 500s
- `preprocessor.py`: trend calculation guards against NaN half-series means before dividing

**Todo List**
- [ ] `chain.py` — remove the unused `client = APIClient(credentials)` line
- [ ] `chain.py` — move `_get_model()` result into a module-level cached variable (lazy-init on first call) so the Watsonx connection is reused across requests
- [ ] `chain.py` — in `_parse_json`, catch `json.JSONDecodeError` and re-raise as `ValueError` with the raw string included in the message
- [ ] `preprocessor.py` — guard `first_half_mean` and `second_half_mean` against NaN before the division

**Relevant Context**
- [`backend/pipeline/chain.py`](backend/pipeline/chain.py)
- [`backend/pipeline/preprocessor.py`](backend/pipeline/preprocessor.py)

**Status** — `[x] done`

---

## Sub-Task 4 — `pipeline/prompts.py` quality

**Intent**
Improve prompt output quality in three targeted ways without changing the 3-step architecture.

**Expected Outcomes**
- Step 1: `"time_range"` field replaced with `"data_shape"` (row/column counts + numeric vs categorical split) — a field that can always be populated from real metadata
- Step 2: insight count is dynamic (3 for small datasets with ≤3 numeric columns, 5 for larger ones) rather than hardcoded at 4
- Step 3: word count target is determined by both audience *and* tone (social_media is always ≤300; analytical tone adds +100 to any other audience)

**Todo List**
- [ ] `prompts.py` — replace `"time_range"` with `"data_shape"` in `SUMMARIZE_HUMAN` template and update `build_summarize_messages` to pass shape info
- [ ] `prompts.py` — update `build_insight_messages` to accept and pass a dynamic `n_insights` count; compute it from the number of numeric columns in the structured data (≤3 → 3 insights, else 5)
- [ ] `prompts.py` — update `build_narrative_messages` and `NARRATIVE_HUMAN` word count logic: social_media → 250, analytical → +100 over base, base is 500

**Relevant Context**
- [`backend/pipeline/prompts.py`](backend/pipeline/prompts.py)
- [`backend/pipeline/chain.py`](backend/pipeline/chain.py) — `build_insight_messages` call site needs updating to pass numeric column count

**Status** — `[x] done`
