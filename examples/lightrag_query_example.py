#!/usr/bin/env python3
"""Example demonstrating LightRAG client usage."""

from python_tools.llm import LightRAGClient


def main() -> None:
    client = LightRAGClient()

    # Health check
    print("Checking health...")
    health = client.health()
    print("Health:", health.get("status", "unknown"))

    # Knowledge query
    prompt = "What is SplitHub's settlement and debt simplification architecture?"
    print(f"\nQuerying: {prompt}\n")
    response = client.query(prompt, mode="local")
    print("=== Response ===")
    print(response)


if __name__ == "__main__":
    main()
