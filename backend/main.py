from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn

from parsers.csv_parser import parse_csv
from parsers.pdf_parser import parse_pdf
from parsers.text_parser import parse_text
from pipeline.chain import run_pipeline

load_dotenv()

app = FastAPI(title="Narrate-AI API", version="1.0.0")

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    # Production: add your Vercel frontend URL after first deploy, e.g.:
     "https://narrate-ai-frontend-1v8ir87qp-andrew-phengthalasy-s-projects.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    structured_data: dict
    audience: str  # "executive", "general_public", "academic", "social_media"
    tone: str      # "analytical", "storytelling", "conversational"


class GenerateResponse(BaseModel):
    headline: str
    narrative: str
    insights: list[dict]
    word_count: int


@app.post("/api/parse")
async def parse_file(file: UploadFile = File(...)):
    """Accept a file upload and return structured data preview."""
    content = await file.read()
    filename = file.filename or ""

    try:
        if filename.endswith(".csv"):
            structured = parse_csv(content)
        elif filename.endswith(".pdf"):
            structured = parse_pdf(content)
        else:
            # Treat as plain text / pasted data
            structured = parse_text(content.decode("utf-8", errors="replace"))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse file: {str(e)}")

    return structured


@app.post("/api/generate", response_model=GenerateResponse)
async def generate_narrative(request: GenerateRequest):
    """Run the 3-step AI pipeline and return a structured narrative."""
    try:
        result = run_pipeline(
            structured_data=request.structured_data,
            audience=request.audience,
            tone=request.tone,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

    return result


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
