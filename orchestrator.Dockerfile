FROM python:3.10-slim

WORKDIR /app

# Install uv tool and project dependencies
RUN pip install uv
COPY pyproject.toml .
RUN uv pip install --system .

# Copy source code
COPY src/ ./src/

# Copy environment variables
COPY .env .env

ENV PYTHONPATH=/app/src

EXPOSE 8080

CMD ["python", "-m", "uvicorn", "qmtl.orchestrator.api:app", "--host", "0.0.0.0", "--port", "8080"]