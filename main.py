"""CLI entry point and HTTP server launcher for the LangChain Fact Checker agent."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

import uvicorn
from dotenv import load_dotenv

from fact_checker.agent import check_fact


def main() -> None:
    load_dotenv(override=True)
    parser = argparse.ArgumentParser(
        description="Fact Checker Agent (LangChain + AWS Bedrock AgentCore Web Search)"
    )
    parser.add_argument(
        "claim",
        nargs="?",
        help="The claim or statement to fact-check. If omitted with --serve, starts the AgentCore Runtime HTTP server.",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Run the FastAPI HTTP server for AgentCore Runtime (/ping and /invocations).",
    )
    parser.add_argument(
        "--host",
        default=os.getenv("HOST", "127.0.0.1"),
        help="Host interface to bind when running with --serve (defaults to 127.0.0.1 locally).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", "8080")),
        help="Port to bind when running with --serve (defaults to 8080).",
    )
    args = parser.parse_args()

    if args.serve:
        uvicorn.run("fact_checker.server:app", host=args.host, port=args.port)
        return

    claim = args.claim or "The Sydney Harbour Bridge was opened in 1955."
    print(f"Claim: {claim}\n" + "-" * 60)
    try:
        verdict = asyncio.run(check_fact(claim))
        print(verdict)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
