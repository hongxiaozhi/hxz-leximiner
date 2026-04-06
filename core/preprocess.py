from __future__ import annotations

import re
from typing import List


def clean_text(text: str) -> str:
    """Normalize whitespace and remove noisy control characters."""
    cleaned = text.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    cleaned = re.sub(r"[^\x00-\x7F]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def split_sentences(text: str) -> List[str]:
    """Split English text into simple sentences for source tracing."""
    normalized = clean_text(text)
    if not normalized:
        return []
    parts = re.split(r"(?<=[.!?])\s+", normalized)
    return [part.strip() for part in parts if part.strip()]