# Narrate-AI

> IBM AI Skills Challenge — July 2025 Hackathon Submission

**Turn raw data into a compelling narrative.** Upload a CSV, PDF, or paste text → select your audience and tone → watch IBM Granite transform it into journalist-quality prose in seconds.

---

## Problem Statement

Data is everywhere, but insight is rare. Analysts, researchers, and executives spend hours turning spreadsheets and reports into readable summaries. Narrate-AI eliminates that gap with a three-step AI pipeline that handles the entire journey from raw numbers to polished story — automatically.

## Solution Description

A full-stack web application where users:

1. **Upload** a CSV, PDF, or paste raw text
2. **Configure** the target audience (Executive, General Public, Academic, Social Media) and tone (Analytical, Storytelling, Conversational)
3. **Generate** — a three-step AI chain runs: data summarization → insight extraction → narrative writing
4. **Export** the narrative as Markdown or copy to clipboard

## AI Approach & Architecture

```
Upload → Parse (Pandas / pdfplumber) → Preprocess (stats, outliers, trends)
       → Step 1: Data Summarizer  (IBM Granite → structured JSON)
       → Step 2: Insight Extractor (IBM Granite → ranked findings)
       → Step 3: Narrative Generator (IBM Granite → final prose)
       → Render in Next.js UI
```

The pipeline is intentionally staged: each step produces a richer representation than the last. Separating *analysis* prompts from *writing* prompts keeps data accuracy high and prevents hallucination.

## Challenge Theme

**Creative Industries** — AI-powered storytelling and content creation tool that transforms how data stories are imagined and produced.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS |
| Backend | Python FastAPI |
| Data parsing | Pandas, pdfplumber |
| AI | IBM Watsonx + Granite (`ibm/granite-13b-instruct-v2`) |
| Dev tool | IBM Bob |

## How IBM Bob Was Used

IBM Bob was used as the primary development tool throughout the entire project — scaffolding the repo structure, writing the three-step AI pipeline, designing the prompt templates, building the FastAPI backend, and implementing the Next.js frontend components.

---

## Getting Started

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in your Watsonx credentials
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # set NEXT_PUBLIC_API_URL if needed
npm run dev
```

Open [http://localhost:3000](http://localhost:8000).

---

## Environment Variables

**Backend (`backend/.env`):**

| Variable | Description |
|---|---|
| `WATSONX_API_KEY` | IBM Cloud API key |
| `WATSONX_URL` | Watsonx endpoint (e.g. `https://us-south.ml.cloud.ibm.com`) |
| `WATSONX_PROJECT_ID` | Watsonx project ID |

**Frontend (`frontend/.env.local`):**

| Variable | Default |
|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` |
