#!/usr/bin/env python3
"""LightRAG Client Utility.

Provides authenticated querying and document insertion against a running LightRAG service.
Supports credentials via environment variables, direct CLI arguments, or local .env configuration.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
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
                            elif k in ("HOST", "PORT") and "LIGHTRAG_URL" not in os.environ:
                                # Keep default localhost if configured
                                pass
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
        """Run a knowledge graph query against LightRAG.

        Args:
            query_text: The natural language prompt/question.
            mode: Query mode ('naive', 'local', 'global', 'hybrid').
            stream: Whether to stream the response (default False).
            timeout: Optional override for request timeout.

        Returns:
            The string response generated by LightRAG.
        """
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


def main() -> None:
    """CLI entry point for querying LightRAG."""
    parser = argparse.ArgumentParser(description="Query LightRAG knowledge graph.")
    parser.add_argument("query", nargs="?", help="Question or query string")
    parser.add_argument(
        "--mode",
        choices=["naive", "local", "global", "hybrid"],
        default="hybrid",
        help="Query mode (default: hybrid)",
    )
    parser.add_argument("--url", default=None, help="Base URL for LightRAG service (e.g. http://localhost:9621)")
    parser.add_argument("--username", default=None, help="LightRAG username")
    parser.add_argument("--password", default=None, help="LightRAG password")
    parser.add_argument("--timeout", type=int, default=90, help="Request timeout in seconds")
    parser.add_argument("--health", action="store_true", help="Check server health and exit")

    args = parser.parse_args()

    client = LightRAGClient(
        base_url=args.url,
        username=args.username,
        password=args.password,
        timeout=args.timeout,
    )

    if args.health:
        try:
            health = client.health()
            print("LightRAG Health Status:")
            print(json.dumps(health, indent=2))
            sys.exit(0)
        except Exception as e:
            print(f"Health check failed: {e}", file=sys.stderr)
            sys.exit(1)

    if not args.query:
        parser.print_help()
        sys.exit(1)

    try:
        print(f"Querying LightRAG (mode: {args.mode})...\n")
        response = client.query(args.query, mode=args.mode, timeout=args.timeout)
        print("=== Response ===")
        print(response)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
