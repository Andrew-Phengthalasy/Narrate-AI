import re

_TEXT_CAP = 8000  # max characters forwarded to the pipeline


def _truncate_at_sentence(text: str, cap: int) -> str:
    """Truncate at the last sentence boundary at or before `cap` chars.

    Falls back to a hard cut if no sentence boundary is found.
    """
    if len(text) <= cap:
        return text
    window = text[:cap]
    match = re.search(r"[.!?](?=\s|$)", window[::-1])
    if match:
        cut = cap - match.start()
        return text[:cut].rstrip()
    return window


def parse_text(raw: str) -> dict:
    """Clean and structure raw pasted text or plain-text data."""
    cleaned = re.sub(r"\r\n", "\n", raw)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned.strip())

    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    paragraphs = cleaned.split("\n\n")

    return {
        "source_type": "text",
        "full_text": _truncate_at_sentence(cleaned, _TEXT_CAP),
        "line_count": len(lines),
        "paragraph_count": len(paragraphs),
        "word_count": len(cleaned.split()),
        "preview": cleaned[:500],
    }
