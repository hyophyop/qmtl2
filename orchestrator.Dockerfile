# syntax=docker/dockerfile:1
FROM python:3.11-slim

RUN pip install uv

WORKDIR /app

COPY pyproject.toml ./
COPY requirements.txt ./
COPY src/ ./src/

RUN uv venv create .venv && .venv/bin/uv pip install -e ./src

ENV PYTHONPATH="/app/src"
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8080

CMD ["uvicorn", "qmtl.orchestrator.main:app", "--host", "0.0.0.0", "--port", "8080"]
