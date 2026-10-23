"""FastAPI HTTP server implementing the Amazon Bedrock AgentCore Runtime HTTP protocol contract."""

from __future__ import annotations

import logging
import os
import signal
import sys
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, Field

from .agent import check_fact

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("fact_checker.server")

MAX_BODY_BYTES = 64 * 1024  # 64 KB limit for input claims


class InvocationRequest(BaseModel):
    """Input payload for AgentCore Runtime /invocations."""

    prompt: str | None = Field(default=None, max_length=8000, description="Claim to verify")
    claim: str | None = Field(default=None, max_length=8000, description="Claim to verify")
    inputText: str | None = Field(default=None, max_length=8000, description="Claim to verify")

    def resolved_claim(self) -> str:
        for candidate in (self.claim, self.prompt, self.inputText):
            if candidate and candidate.strip():
                return candidate.strip()
        raise ValueError("Request body must include a non-empty 'claim', 'prompt', or 'inputText' field.")


class InvocationResponse(BaseModel):
    """Output payload returned from /invocations."""

    verdict: str
    model: str
    runtime_id: str | None = None


app = FastAPI(
    title="Fact Checker Agent (LangChain + AWS Bedrock AgentCore)",
    version="0.1.0",
)


@app.middleware("http")
async def security_and_size_middleware(request: Request, call_next: Any) -> Response:
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_BODY_BYTES:
        return Response(content='{"detail":"Request body too large"}', status_code=413, media_type="application/json")

    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/ping")
@app.get("/health")
async def ping() -> dict[str, str]:
    """AgentCore Runtime HTTP protocol health check endpoint."""
    return {"status": "Healthy"}


@app.post("/invocations", response_model=InvocationResponse)
async def invocations(payload: InvocationRequest) -> InvocationResponse:
    """AgentCore Runtime HTTP protocol invocation endpoint."""
    try:
        claim = payload.resolved_claim()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    logger.info("Fact-checking claim via AgentCore Gateway Web Search (length=%d chars)", len(claim))
    try:
        verdict = await check_fact(claim=claim)
    except Exception as exc:
        logger.exception("Error while executing fact check")
        raise HTTPException(status_code=500, detail=f"Fact check execution error: {exc}") from exc

    active_model = (
        os.getenv("GOOGLE_MODEL_ID", "gemini-3.5-flash")
        if os.getenv("LLM_PROVIDER", "google").lower() in ("google", "gemini", "vertexai")
        else os.getenv("BEDROCK_MODEL_ID", "us.amazon.nova-2-lite-v1:0")
    )
    return InvocationResponse(
        verdict=verdict,
        model=active_model,
        runtime_id=os.getenv("RUNTIME_ID"),
    )


def _handle_sigterm(signum: int, frame: Any) -> None:
    logger.info("Received signal %d, shutting down gracefully", signum)
    sys.exit(0)


signal.signal(signal.SIGTERM, _handle_sigterm)
