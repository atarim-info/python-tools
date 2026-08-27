#!/usr/bin/env python3
"""LightRAG Model Context Protocol (MCP) Server.

Standard JSON-RPC 2.0 stdio MCP server for LightRAG knowledge graph integration.
Works with standard Python 3.8+ with zero external package dependencies.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List, Optional

# Ensure sibling imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from lightrag_client import LightRAGClient
except ImportError:
    # Inline minimal client if lightrag_client cannot be resolved
    class LightRAGClient:  # type: ignore
        DEFAULT_URL = "http://localhost:9621"
        KNOWN_ENV_LOCATIONS = [
            r"d:\MyProjects\SharedProjects\Ubuntu-24.04_WSL\devops\lightrag\.env",
            os.path.expanduser("~/.lightrag/.env"),
            ".env",
        ]

        def __init__(self, base_url: Optional[str] = None, timeout: int = 60) -> None:
            import urllib.parse
            import urllib.request

            self.base_url = (base_url or os.environ.get("LIGHTRAG_URL") or self.DEFAULT_URL).rstrip("/")
            self.username = os.environ.get("LIGHTRAG_USERNAME")
            self.password = os.environ.get("LIGHTRAG_PASSWORD")
            self.timeout = timeout
            self._token: Optional[str] = None
            if not (self.username and self.password):
                for path in self.KNOWN_ENV_LOCATIONS:
                    if os.path.exists(path):
                        with open(path, "r", encoding="utf-8") as f:
                            for line in f:
                                if "=" in line and not line.strip().startswith("#"):
                                    k, v = line.strip().split("=", 1)
                                    k, v = k.strip(), v.strip().strip('"').strip("'")
                                    if k == "LIGHTRAG_USERNAME" and not self.username:
                                        self.username = v
                                    elif k == "LIGHTRAG_PASSWORD" and not self.password:
                                        self.password = v
                                    elif k == "AUTH_ACCOUNTS" and not (self.username and self.password) and ":" in v:
                                        self.username, self.password = v.split(":", 1)

        def authenticate(self) -> str:
            import urllib.parse
            import urllib.request
            if self._token:
                return self._token
            url = f"{self.base_url}/login"
            data = urllib.parse.urlencode({"username": self.username, "password": self.password}).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                self._token = res.get("access_token")
                return self._token

        def health(self) -> Dict[str, Any]:
            import urllib.request
            req = urllib.request.Request(f"{self.base_url}/health")
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))

        def query(self, query_text: str, mode: str = "hybrid", timeout: Optional[int] = None) -> str:
            import urllib.request
            token = self.authenticate()
            req = urllib.request.Request(
                f"{self.base_url}/query",
                data=json.dumps({"query": query_text, "mode": mode, "stream": False}).encode("utf-8"),
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
            )
            with urllib.request.urlopen(req, timeout=timeout or self.timeout) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                return res.get("response", res) if isinstance(res, dict) else str(res)

        def insert_text(self, text: str, description: Optional[str] = None, file_source: Optional[str] = None) -> Dict[str, Any]:
            import urllib.request
            token = self.authenticate()
            payload: Dict[str, Any] = {"text": text}
            if description:
                payload["description"] = description
            if file_source:
                payload["file_source"] = file_source
            req = urllib.request.Request(
                f"{self.base_url}/documents/text",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))


TOOLS_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "name": "query_knowledge_graph",
        "description": "Query the LightRAG second-brain knowledge graph to retrieve architecture decisions, domain models, and platform specifications.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language query or question about the platform, services, or architecture.",
                },
                "mode": {
                    "type": "string",
                    "enum": ["hybrid", "local", "global", "naive"],
                    "default": "hybrid",
                    "description": "Search mode: 'hybrid' (vector + entity graph), 'local' (entity/component focus), 'global' (system-wide summaries), or 'naive' (vector search).",
                },
                "timeout": {
                    "type": "integer",
                    "default": 90,
                    "description": "Request timeout in seconds.",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "check_lightrag_health",
        "description": "Check the health, version, and pipeline status of the LightRAG knowledge graph server.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "insert_document_text",
        "description": "Ingest design documents or markdown specifications into the LightRAG knowledge graph.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Raw markdown or text content to index into the second-brain graph.",
                },
                "description": {
                    "type": "string",
                    "description": "Optional title or summary description of the document.",
                },
                "file_source": {
                    "type": "string",
                    "description": "Optional source file path or identifier.",
                },
            },
            "required": ["text"],
        },
    },
]


def handle_tool_call(name: str, arguments: Dict[str, Any]) -> str:
    """Execute the requested tool and return a string result."""
    client = LightRAGClient()
    if name == "query_knowledge_graph":
        query_text = arguments.get("query", "")
        mode = arguments.get("mode", "hybrid")
        timeout = arguments.get("timeout", 90)
        return client.query(query_text=query_text, mode=mode, timeout=timeout)

    elif name == "check_lightrag_health":
        health = client.health()
        return json.dumps(health, indent=2)

    elif name == "insert_document_text":
        text = arguments.get("text", "")
        description = arguments.get("description", "")
        file_source = arguments.get("file_source", "")
        res = client.insert_text(text=text, description=description or None, file_source=file_source or None)
        return json.dumps(res, indent=2)

    else:
        raise ValueError(f"Unknown tool: {name}")


def send_response(response: Dict[str, Any]) -> None:
    """Send a JSON-RPC response to stdout followed by newline."""
    raw = json.dumps(response)
    sys.stdout.write(raw + "\n")
    sys.stdout.flush()


def main() -> None:
    """Run the MCP JSON-RPC stdio event loop."""
    sys.stderr.write("LightRAG MCP Server started on stdio\n")
    sys.stderr.flush()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            req = json.loads(line)
        except json.JSONDecodeError as e:
            sys.stderr.write(f"Invalid JSON: {e}\n")
            continue

        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        # Handle MCP JSON-RPC methods
        if method == "initialize":
            send_response({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {
                            "listChanged": False,
                        },
                    },
                    "serverInfo": {
                        "name": "lightrag-mcp-server",
                        "version": "1.0.0",
                    },
                },
            })

        elif method == "notifications/initialized":
            # Client notification acknowledgment, no response required
            pass

        elif method == "ping":
            send_response({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {},
            })

        elif method == "tools/list":
            send_response({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": TOOLS_DEFINITIONS,
                },
            })

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            try:
                result_text = handle_tool_call(tool_name, tool_args)
                send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": str(result_text),
                            }
                        ],
                        "isError": False,
                    },
                })
            except Exception as ex:
                send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Tool execution failed: {ex}",
                            }
                        ],
                        "isError": True,
                    },
                })

        else:
            if req_id is not None:
                send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method '{method}' not found",
                    },
                })


if __name__ == "__main__":
    main()
