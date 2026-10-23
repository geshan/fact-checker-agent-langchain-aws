# Multi-stage ARM64 Dockerfile for Amazon Bedrock AgentCore Runtime (HTTP protocol)
FROM --platform=linux/arm64 ghcr.io/astral-sh/uv:0.11.7 AS uv_bin

FROM --platform=linux/arm64 python:3.12.4-slim AS builder
COPY --from=uv_bin /uv /uvx /bin/
WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY fact_checker ./fact_checker
COPY main.py README.md ./
RUN uv sync --frozen --no-dev

FROM --platform=linux/arm64 python:3.12.4-slim
RUN useradd -r -u 1001 appuser
WORKDIR /app
COPY --from=builder --chown=appuser:appuser /app /app
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED="1"
USER appuser
EXPOSE 8080

# Binds to 0.0.0.0 for AgentCore internal routing. Do NOT expose directly to the internet.
CMD ["uvicorn", "fact_checker.server:app", "--host", "0.0.0.0", "--port", "8080"]
