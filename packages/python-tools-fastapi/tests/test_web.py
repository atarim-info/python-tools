"""Unit / contract tests for python_tools.web (PT-07)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from python_tools.config import BaseServiceSettings, Environment, ServiceMode
from python_tools.obs import HealthRegistry
from python_tools.web import (
    CONFLICT_ETAG,
    EtagMismatch,
    check_if_match,
    create_app,
    error_body,
    extract_idempotency_key,
    make_etag,
    paginate,
)


def _settings() -> BaseServiceSettings:
    return BaseServiceSettings(
        service_name="web-test",
        environment=Environment.DEV,
        mode=ServiceMode.WEB,
        log_level="INFO",
    )


def test_error_body_shape() -> None:
    body = error_body("not_found", "missing", request_id="r1", details={"id": "x"})
    assert body == {
        "error": {"code": "not_found", "message": "missing", "details": {"id": "x"}, "request_id": "r1"}
    }


def test_etag_helpers() -> None:
    assert make_etag(3) == 'W/"3"'
    check_if_match('W/"3"', 'W/"3"')
    try:
        check_if_match('W/"3"', 'W/"2"')
        raise AssertionError("expected EtagMismatch")
    except EtagMismatch:
        pass


def test_idempotency_and_pagination() -> None:
    assert extract_idempotency_key({"Idempotency-Key": " abc "}) == "abc"
    assert extract_idempotency_key({}) is None
    page = paginate(list(range(5)), limit=2, cursor="2")
    assert page.items == [2, 3]
    assert page.has_more is True
    assert page.next_cursor == "4"


def test_create_app_health_and_request_id() -> None:
    health = HealthRegistry()
    health.register("always", lambda: True)
    app = create_app(title="t", version="9.9.9", settings=_settings(), health_registry=health)
    client = TestClient(app)

    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["version"] == "9.9.9"

    r = client.get("/readyz")
    assert r.status_code == 200
    assert r.json()["status"] == "ready"

    r = client.get("/metrics")
    assert r.status_code == 200
    assert "text/plain" in r.headers["content-type"]

    r = client.get("/healthz", headers={"X-Request-ID": "fixed-id"})
    assert r.headers["X-Request-ID"] == "fixed-id"


def test_exception_map_etag() -> None:
    app = create_app(title="t", settings=_settings())

    @app.get("/boom")
    async def boom() -> None:
        raise EtagMismatch("etag mismatch")

    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/boom")
    assert r.status_code == 412
    assert r.json()["error"]["code"] == CONFLICT_ETAG
