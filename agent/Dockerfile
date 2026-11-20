# Local Compose agent: in-memory LangGraph server (same as `langgraph dev`).
# No LangSmith deploy license / Redis — Gemini key comes from Compose env.

FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.9.5 /uv /usr/local/bin/uv

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PORT=2024

# Project metadata first for better layer caching
COPY pyproject.toml README.md langgraph.json ./
COPY src ./src
RUN mkdir -p config \
    && touch config/.env.local

# Editable install + inmem CLI (dev extra)
RUN uv pip install --system --no-cache -e ".[dev]"

EXPOSE 2024

CMD ["langgraph", "dev", "--host", "0.0.0.0", "--port", "2024", "--no-browser", "--no-reload"]
