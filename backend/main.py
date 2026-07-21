import json
import logging
import time
import uuid
from collections import defaultdict
from typing import Literal

from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn

from parsers.csv_parser import parse_csv
from parsers.pdf_parser import parse_pdf
from parsers.text_parser import parse_text
from pipeline.chain import run_pipeline

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s %(message)s",
)
logger = logging.getLogger("narrate-ai")

app = FastAPI(title="Narrate-AI API", version="1.0.0")

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://narrate-ai-frontend-1v8ir87qp-andrew-phengthalasy-s-projects.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Size limits ───────────────────────────────────────────────────────────────
MAX_UPLOAD_BYTES = 10 * 1024 * 1024   # 10 MB
MAX_PAYLOAD_BYTES = 50 * 1024          # 50 KB

# ── Rate limiting (token bucket, in-memory) ───────────────────────────────────
# Applies to /api/generate only — each Watsonx call has real cost.
# Each IP gets RATE_LIMIT_BURST tokens; one token is consumed per request.
# Tokens refill at RATE_LIMIT_RATE per second up to the burst cap.
RATE_LIMIT_RATE = 1 / 10      # 1 token per 10 seconds → 6 requests / minute
RATE_LIMIT_BURST = 3          # allow short bursts of up to 3 back-to-back requests

_buckets: dict[str, dict] = defaultdict(lambda: {"tokens": RATE_LIMIT_BURST, "last": time.monotonic()})


def _check_rate_limit(ip: str) -> bool:
    """Return True if the request is allowed, False if rate-limited."""
    bucket = _buckets[ip]
    now = time.monotonic()
    elapsed = now - bucket["last"]
    bucket["tokens"] = min(RATE_LIMIT_BURST, bucket["tokens"] + elapsed * RATE_LIMIT_RATE)
    bucket["last"] = now
    if bucket["tokens"] >= 1:
        bucket["tokens"] -= 1
        return True
    return False


# ── Magic-byte file type detection ───────────────────────────────────────────
_MAGIC = {b"%PDF": "pdf"}


def _detect_type(content: bytes, filename: str) -> str:
    """Return 'csv', 'pdf', or 'text' based on magic bytes then filename."""
    for magic, ftype in _MAGIC.items():
        if content.startswith(magic):
            return ftype
    if filename.endswith(".csv"):
        return "csv"
    return "text"


# ── Request ID middleware ─────────────────────────────────────────────────────
@app.middleware("http")
async def attach_request_id(request: Request, call_next):
    """Attach a unique request ID to every request and propagate it in the response."""
    request_id = str(uuid.uuid4())[:8]
    # Make it available to route handlers via request.state
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# ── Models ────────────────────────────────────────────────────────────────────
class GenerateRequest(BaseModel):
    structured_data: dict
    audience: Literal["executive", "general_public", "academic", "social_media"]
    tone: Literal["analytical", "storytelling", "conversational"]


class GenerateResponse(BaseModel):
    headline: str
    narrative: str
    insights: list[dict]
    word_count: int


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/parse")
async def parse_file(request: Request, file: UploadFile = File(...)):
    """Accept a file upload and return structured data preview."""
    rid = getattr(request.state, "request_id", "-")
    content = await file.read()
    filename = file.filename or ""

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
        )

    file_type = _detect_type(content, filename)
    logger.info("[%s] parse '%s' detected=%s bytes=%d", rid, filename, file_type, len(content))

    try:
        if file_type == "csv":
            structured = parse_csv(content)
        elif file_type == "pdf":
            structured = parse_pdf(content)
        else:
            structured = parse_text(content.decode("utf-8", errors="replace"))
    except Exception as e:
        logger.exception("[%s] parse failed for '%s'", rid, filename)
        raise HTTPException(status_code=422, detail=f"Failed to parse file: {str(e)}")

    logger.info("[%s] parse ok source_type=%s", rid, structured.get("source_type"))
    return structured


@app.post("/api/generate", response_model=GenerateResponse)
async def generate_narrative(request: Request, body: GenerateRequest):
    """Run the 3-step AI pipeline and return a structured narrative."""
    rid = getattr(request.state, "request_id", "-")
    client_ip = request.client.host if request.client else "unknown"

    if not _check_rate_limit(client_ip):
        logger.warning("[%s] rate limited ip=%s", rid, client_ip)
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please wait a few seconds before trying again.",
        )

    payload_size = len(json.dumps(body.structured_data))
    if payload_size > MAX_PAYLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"structured_data too large ({payload_size} bytes). Maximum is {MAX_PAYLOAD_BYTES // 1024} KB.",
        )

    logger.info("[%s] generate audience=%s tone=%s payload=%d", rid, body.audience, body.tone, payload_size)

    try:
        result = await run_pipeline(
            structured_data=body.structured_data,
            audience=body.audience,
            tone=body.tone,
            request_id=rid,
        )
    except Exception as e:
        logger.exception("[%s] pipeline error audience=%s tone=%s", rid, body.audience, body.tone)
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

    logger.info("[%s] generate ok headline=%r words=%d", rid, result["headline"][:60], result["word_count"])
    return result


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
