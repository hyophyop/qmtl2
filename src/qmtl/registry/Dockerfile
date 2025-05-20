# syntax=docker/dockerfile:1
FROM python:3.11-slim

RUN pip install uv

WORKDIR /app

COPY ../../pyproject.toml ./
COPY ../../requirements.txt ./
COPY ../../src/ ./src/

RUN uv pip install --system -e ./src

ENV PYTHONPATH="/app/src"

EXPOSE 8000

CMD ["uvicorn", "qmtl.dag_manager.registry.api:app", "--host", "0.0.0.0", "--port", "8000"]
