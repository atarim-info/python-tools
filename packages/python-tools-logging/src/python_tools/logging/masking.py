"""PII masking processor for structlog.

Masks emails, phone numbers, national IDs, and free-text document/CV bodies so they
never reach the log sink in full. Applied as a structlog processor, so masking is
enforced centrally rather than at every call site.
"""

from __future__ import annotations

import re
from typing import Any

MASK = "***"

# Keys whose values are treated as free-text bodies and never logged in full.
SENSITIVE_KEYS: frozenset[str] = frozenset(
    {
        "cv",
        "cv_body",
        "resume",
        "resume_body",
        "document",
        "document_body",
        "body",
        "content",
        "text",
    }
)

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
# National ID: exactly 9 digits (e.g. Israeli teudat zehut), not part of a longer run.
_NATIONAL_ID_RE = re.compile(r"(?<!\d)\d{9}(?!\d)")
# Phone: 8+ digits with optional separators / country code.
_PHONE_RE = re.compile(r"(?<![\w])\+?\d[\d\s\-().]{7,}\d(?![\w])")


def _mask_text(text: str) -> str:
    text = _EMAIL_RE.sub(lambda m: f"{MASK}@{m.group(1)}", text)
    text = _NATIONAL_ID_RE.sub(MASK, text)
    text = _PHONE_RE.sub(MASK, text)
    return text


def _redact_body(value: Any) -> str:
    if isinstance(value, str):
        return f"<redacted len={len(value)}>"
    return f"<redacted {type(value).__name__}>"


def mask_pii(logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """structlog processor: mask PII in the event dict in place and return it."""

    for key, value in list(event_dict.items()):
        if key in SENSITIVE_KEYS:
            event_dict[key] = _redact_body(value)
        elif isinstance(value, str):
            event_dict[key] = _mask_text(value)
    return event_dict
