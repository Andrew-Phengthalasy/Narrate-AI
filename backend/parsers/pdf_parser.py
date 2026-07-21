import io
import re
import pdfplumber

_TEXT_CAP = 8000  # max characters sent to the model


def _truncate_at_sentence(text: str, cap: int) -> str:
    """Truncate text at the last sentence boundary at or before `cap` chars.

    Falls back to a hard cut if no sentence boundary is found.
    """
    if len(text) <= cap:
        return text
    window = text[:cap]
    # Find the last sentence-ending punctuation followed by whitespace or end
    match = re.search(r"[.!?](?=\s|$)", window[::-1])
    if match:
        cut = cap - match.start()
        return text[:cut].rstrip()
    return window  # hard cut fallback


def parse_pdf(content: bytes) -> dict:
    """Extract text and tables from a PDF and return a structured dict."""
    text_pages = []
    tables = []
    total_pages = 0

    with pdfplumber.open(io.BytesIO(content)) as pdf:
        total_pages = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            if text.strip():
                text_pages.append({"page": i + 1, "text": text.strip()})

            page_tables = page.extract_tables()
            for table in page_tables:
                if table:
                    # Replace None cells with "" so the table serialises cleanly
                    # into the model prompt without bare `null` values.
                    sanitised = [
                        ["" if cell is None else str(cell) for cell in row]
                        for row in table
                    ]
                    tables.append({"page": i + 1, "data": sanitised})

    full_text = "\n\n".join(p["text"] for p in text_pages)
    truncated_text = _truncate_at_sentence(full_text, _TEXT_CAP)

    return {
        "source_type": "pdf",
        "page_count": total_pages,
        "text_page_count": len(text_pages),
        "full_text": truncated_text,
        "tables": tables[:5],           # first 5 tables
        "word_count": len(full_text.split()),
    }
