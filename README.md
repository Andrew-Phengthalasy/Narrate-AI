# Narrate-AI

> **IBM Bob Challenge — July 2025**  ·  Theme: *Reimagine Creative Industries with AI*

**Turn raw data into journalist-quality prose in seconds.** Upload a CSV, PDF, or paste text, then choose your audience and tone and watch IBM Granite produce a polished, insight-driven narrative automatically.

---

## 1. Problem Statement

Data is everywhere, but insight is rare.

Analysts, researchers, and executives spend hours converting spreadsheets and reports into readable summaries for stakeholders who will never open a pivot table. That translation from numbers to narrative is slow, expensive, and inconsistent. A single data story can take a skilled analyst half a day to write; a newsroom team cannot sustain that pace across hundreds of datasets.

NarrateAI eliminates that gap. It automates the entire journey from raw data to publication-ready prose analysis, insight ranking, and writing in a single pipeline that takes seconds, not hours.

---

## 2. Solution Description

A full-stack AI web application with a three-step pipeline:

| Step | What happens |
|------|-------------|
| **Upload** | User provides a CSV, PDF, or raw text paste |
| **Configure** | Select target audience (Executive / General Public / Academic / Social Media) and tone (Analytical / Storytelling / Conversational) |
| **Generate** | A three-stage AI chain runs end-to-end and returns a structured narrative |
| **Export** | Download as Markdown or copy to clipboard |

The output is not a bullet-point summary. It is a full prose narrative, the kind a journalist or data analyst would write with a headline, introduction, insight paragraphs, and a closing statement, all calibrated to the selected audience and tone.

---

## 3. Challenge Theme

**Reimagine Creative Industries with AI**

Writing has always been the bottleneck between data and decisions. Every earnings report, research study, and market analysis needs a human storyteller to cross that gap; someone who can look at a table of numbers and say *what it means*.

NarrateAI makes that skill available to anyone, at any scale. It does not replace the journalist or analyst; it removes the mechanical part of their job so they can spend their time on judgment, not transcription.

This directly reimagines the data journalism and communications workflow: a single tool replacing what would otherwise require a senior writer, a data analyst, and multiple revision cycles.

---

## 4. AI Approach & Architecture

### The Three-Stage Pipeline

Every request runs through a sequential reasoning chain. Each stage produces a richer, more structured representation than the last. Separating *analysis* prompts from *writing* prompts keeps data accuracy high and prevents hallucination.

```
Upload → Parse (Pandas / pdfplumber)
       → Preprocess (statistics, outliers, date-sorted trends)
       ↓
  Stage 1 — Data Summarizer         (IBM Granite → structured JSON)
    · Identifies key metrics, time range, data shape
    · Produces a machine-readable summary for Stage 2
       ↓
  Stage 2 — Insight Extractor       (IBM Granite → ranked findings)
    · Reads the summary and raw data
    · Returns ranked insights — most newsworthy first
    · Stage is isolated: pipeline continues even if extraction fails
       ↓
  Stage 3 — Narrative Generator     (IBM Granite → final prose)
    · Ingests summary + insights + user config (audience, tone)
    · Writes a publication-ready narrative in the requested voice
       ↓
  Render → Next.js UI (ranked insight cards + article view)
```

### Why IBM Granite

IBM Granite (`ibm/granite-13b-instruct-v2`) was selected for its instruction-following consistency on structured JSON extraction tasks. The pipeline depends on machine-readable intermediate outputs between stages; a model that drifts from the schema breaks the chain. Granite's deterministic greedy decoding keeps inter-stage outputs stable.

### Prompt Design

Each stage uses a purpose-built prompt template in [`backend/pipeline/prompts.py`](backend/pipeline/prompts.py):

- **Stage 1** — instructs the model to return a strict JSON schema with `title`, `key_metrics`, `time_range`, `data_shape`, and `highlights`
- **Stage 2** — dynamically scales the number of requested insights to the data density (derived from `key_metrics` count)
- **Stage 3** — injects audience-specific writing instructions and tone profiles before the final prose pass

### Security & Production Hardening

| Feature | Detail |
|---------|--------|
| File type validation | Magic-byte detection (not just extension) |
| Size limits | 10 MB upload cap, 50 KB JSON payload cap |
| Rate limiting | Token bucket per IP — 3 burst / 6 per minute |
| Prompt injection guard | `_sanitise_data()` strips control characters from all user-supplied content before it enters any prompt |
| Request tracing | UUID request ID attached to every log line |
| Async execution | Watsonx calls run in a thread executor — no event loop blocking |

---

## 5. Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16 (App Router), TypeScript |
| Backend | Python 3.12, FastAPI |
| Data parsing | Pandas, pdfplumber |
| AI model | IBM Watsonx · `ibm/granite-13b-instruct-v2` |
| Deployment | Vercel (two separate projects — backend + frontend) |
| Built with | IBM Bob |

---

## 6. How IBM Bob Was Used

Every line of this project was written with IBM Bob as the active engineering partner — not as an autocomplete tool, but as a full-stack engineer working through the problem alongside the developer.

Specifically, IBM Bob:

- Designed the three-stage pipeline architecture and prompt templates from scratch
- Built the entire FastAPI backend including middleware, rate limiting, and file parsers
- Scaffolded and implemented all Next.js frontend components and the CSS design system
- Diagnosed and fixed every production bug across both frontend and backend (async issues, pandas deprecation, JSON serialisation of numpy types, Vercel Python path resolution, and more)
- Wrote the Vercel deployment configuration for both projects, including the rewrite proxy that eliminates CORS in production
- Performed systematic multi-pass code reviews of the full codebase, fixing issues proactively before they surfaced in production

The entire submission — architecture, code, prompts, deployment, and documentation — was produced through Bob conversations.

---

## 7. Getting Started (Local)

### Prerequisites

- Python 3.10+
- Node.js 18+
- An [IBM Cloud](https://cloud.ibm.com) account with a Watsonx project

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in WATSONX_API_KEY, WATSONX_URL, WATSONX_PROJECT_ID
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
# create frontend/.env.local with:
# NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

---

## 8. Deploying to Vercel

The project deploys as two separate Vercel projects. The frontend proxies all `/api/*` requests to the backend via a Vercel rewrite — no CORS configuration is required in production.

### Step 1 — Add Vercel secrets (once)

```bash
vercel secrets add watsonx-api-key     "YOUR_IBM_CLOUD_API_KEY"
vercel secrets add watsonx-url         "https://us-south.ml.cloud.ibm.com"
vercel secrets add watsonx-project-id  "YOUR_PROJECT_ID"
```

### Step 2 — Deploy the backend

```bash
cd backend
npx vercel --prod
```

Set the **root directory** to `backend/` when prompted. The environment variables are pre-wired in [`backend/vercel.json`](backend/vercel.json) and will resolve from the secrets added above.

Note the deployed URL (e.g. `https://narrate-ai-backend.vercel.app`).

### Step 3 — Point the frontend at your backend

Edit [`frontend/vercel.json`](frontend/vercel.json) and set the `destination` to your backend URL:

```json
{
  "version": 2,
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://<your-backend>.vercel.app/api/:path*"
    }
  ]
}
```

### Step 4 — Deploy the frontend

```bash
cd frontend
npx vercel --prod
```

Set the **root directory** to `frontend/`. No environment variables are needed — all routing is handled by the rewrite.

---

## 9. Environment Variables

### Backend (`backend/.env`)

| Variable | Description |
|----------|-------------|
| `WATSONX_API_KEY` | IBM Cloud API key |
| `WATSONX_URL` | Watsonx regional endpoint (e.g. `https://us-south.ml.cloud.ibm.com`) |
| `WATSONX_PROJECT_ID` | Watsonx project ID |

### Frontend (`frontend/.env.local`) — local dev only

| Variable | Default |
|----------|---------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` |

Not required in production — the Vercel rewrite handles routing without exposing the backend URL to the client.

---

## 10. Project Structure

```
Narrate-AI/
├── backend/
│   ├── api/
│   │   └── index.py          # Vercel serverless entry point
│   ├── parsers/
│   │   ├── csv_parser.py     # Pandas CSV → structured summary
│   │   ├── pdf_parser.py     # pdfplumber PDF → text + metadata
│   │   └── text_parser.py    # Raw text → truncated, cleaned input
│   ├── pipeline/
│   │   ├── chain.py          # Three-stage async pipeline orchestrator
│   │   ├── preprocessor.py   # Statistics, outliers, trend computation
│   │   └── prompts.py        # All LLM prompt templates
│   ├── main.py               # FastAPI app — routes, middleware, rate limiting
│   ├── requirements.txt
│   └── vercel.json
└── frontend/
    ├── src/
    │   ├── app/
    │   │   ├── page.tsx      # Upload + configure flow (steps 1–2)
    │   │   ├── result/
    │   │   │   └── page.tsx  # Narrative viewer
    │   │   ├── layout.tsx
    │   │   └── globals.css   # Design token system
    │   ├── components/
    │   │   ├── FileUpload.tsx
    │   │   ├── ConfigPanel.tsx
    │   │   └── NarrativeViewer.tsx
    │   └── lib/
    │       ├── api.ts         # Typed fetch client with timeout + error handling
    │       └── config.ts      # Audience / tone option definitions
    ├── vercel.json            # Rewrite proxy → backend
    └── package.json
```
