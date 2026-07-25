from __future__ import annotations

from python_tools.logging.masking import mask_pii


def _mask(**fields: object) -> dict[str, object]:
    return mask_pii(None, "info", dict(fields))


def test_email_masked_keeps_domain() -> None:
    out = _mask(event="login", user="dana@example.com")
    assert out["user"] == "***@example.com"


def test_phone_masked() -> None:
    out = _mask(event="call", phone="+972 50-123-4567")
    assert "50-123-4567" not in str(out["phone"])
    assert "***" in str(out["phone"])


def test_national_id_masked() -> None:
    out = _mask(event="verify", note="id 123456789 checked")
    assert "123456789" not in str(out["note"])


def test_free_text_body_redacted() -> None:
    out = _mask(event="parse", cv_body="Long CV text with dana@example.com inside")
    assert out["cv_body"] == "<redacted len=41>"


def test_hebrew_body_not_leaked() -> None:
    hebrew = "קורות חיים של דנה עם אימייל dana@example.com וטלפון 0501234567"
    out = _mask(event="parse", document=hebrew)
    assert "דנה" not in str(out["document"])
    assert str(out["document"]).startswith("<redacted len=")


def test_hebrew_message_masks_embedded_pii() -> None:
    hebrew_msg = "המשתמש dana@example.com התחבר"
    out = _mask(event=hebrew_msg)
    assert "dana@example.com" not in str(out["event"])
    assert "***@example.com" in str(out["event"])
