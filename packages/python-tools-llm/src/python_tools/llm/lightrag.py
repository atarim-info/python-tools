"""LightRAG client module for python-tools-llm.

Provides authenticated graph querying and document ingestion integration for LightRAG.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional


class LightRAGClient:
    """Client for interacting with LightRAG API with authentication support."""

    DEFAULT_URL = "http://localhost:9621"
    KNOWN_ENV_LOCATIONS = [
        r"d:\MyProjects\SharedProjects\Ubuntu-24.04_WSL\devops\lightrag\.env",
        os.path.expanduser("~/.lightrag/.env"),
        ".env",
    ]

    def __init__(
        self,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 60,
    ) -> None:
        self.base_url = (base_url or os.environ.get("LIGHTRAG_URL") or self.DEFAULT_URL).rstrip("/")
        self.username = username or os.environ.get("LIGHTRAG_USERNAME")
        self.password = password or os.environ.get("LIGHTRAG_PASSWORD")
        self.timeout = timeout
        self._token: Optional[str] = None

        if not (self.username and self.password):
            self._load_from_known_env_files()

    def _load_from_known_env_files(self) -> None:
        """Attempt to discover credentials from known local .env locations."""
        for path in self.KNOWN_ENV_LOCATIONS:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith("#") or "=" not in line:
                                continue
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip('"').strip("'")
                            if k == "LIGHTRAG_USERNAME" and not self.username:
                                self.username = v
                            elif k == "LIGHTRAG_PASSWORD" and not self.password:
                                self.password = v
                            elif k == "AUTH_ACCOUNTS" and not (self.username and self.password):
                                if ":" in v:
                                    u, p = v.split(":", 1)
                                    self.username = u
                                    self.password = p
                    if self.username and self.password:
                        break
                except Exception:
                    continue

    def authenticate(self) -> str:
        """Authenticate with the LightRAG instance and retrieve JWT access token."""
        if self._token:
            return self._token

        if not (self.username and self.password):
            raise ValueError(
                "LightRAG username/password not provided. Set LIGHTRAG_USERNAME and "
                "LIGHTRAG_PASSWORD environment variables or pass them explicitly."
            )

        url = f"{self.base_url}/login"
        data = urllib.parse.urlencode({"username": self.username, "password": self.password}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                self._token = result.get("access_token")
                if not self._token:
                    raise ValueError(f"No access token returned: {result}")
                return self._token
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Authentication failed (HTTP {e.code}): {err_body}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to connect to LightRAG at {url}: {e}") from e

    def health(self) -> Dict[str, Any]:
        """Check LightRAG server health."""
        url = f"{self.base_url}/health"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def query(
        self,
        query_text: str,
        mode: str = "hybrid",
        stream: bool = False,
        timeout: Optional[int] = None,
    ) -> str:
        """Run a knowledge graph query against LightRAG."""
        token = self.authenticate()
        url = f"{self.base_url}/query"
        payload = {
            "query": query_text,
            "mode": mode,
            "stream": stream,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
        )
        t = timeout or self.timeout
        try:
            with urllib.request.urlopen(req, timeout=t) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                if isinstance(res, dict) and "response" in res:
                    return str(res["response"])
                return json.dumps(res, indent=2)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Query failed (HTTP {e.code}): {err_body}") from e
        except Exception as e:
            raise RuntimeError(f"Query request failed: {e}") from e

    def insert_text(self, text: str, description: Optional[str] = None, file_source: Optional[str] = None) -> Dict[str, Any]:
        """Insert arbitrary text content into the LightRAG knowledge graph."""
        token = self.authenticate()
        url = f"{self.base_url}/documents/text"
        payload: Dict[str, Any] = {"text": text}
        if description:
            payload["description"] = description
        if file_source:
            payload["file_source"] = file_source
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
