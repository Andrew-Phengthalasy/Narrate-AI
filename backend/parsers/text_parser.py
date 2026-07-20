import re


def parse_text(raw: str) -> dict:
    """Clean and structure raw pasted text or plain-text data."""
    cleaned = re.sub(r"\r\n", "\n", raw)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned.strip())

    lines = [l.strip() for l in cleaned.splitlines() if l.strip()]
    paragraphs = cleaned.split("\n\n")

    return {
        "source_type": "text",
        "full_text": cleaned[:8000],
        "line_count": len(lines),
        "paragraph_count": len(paragraphs),
        "word_count": len(cleaned.split()),
        "preview": cleaned[:500],
    }
