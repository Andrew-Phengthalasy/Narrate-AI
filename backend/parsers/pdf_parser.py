import io
import pdfplumber


def parse_pdf(content: bytes) -> dict:
    """Extract text and tables from a PDF and return a structured dict."""
    text_pages = []
    tables = []

    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            if text.strip():
                text_pages.append({"page": i + 1, "text": text.strip()})

            page_tables = page.extract_tables()
            for table in page_tables:
                if table:
                    tables.append({"page": i + 1, "data": table})

    full_text = "\n\n".join(p["text"] for p in text_pages)

    return {
        "source_type": "pdf",
        "page_count": len(text_pages),
        "full_text": full_text[:8000],  # cap to avoid token overflow
        "tables": tables[:5],           # first 5 tables
        "word_count": len(full_text.split()),
    }
