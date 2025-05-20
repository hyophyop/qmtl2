# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Install uv (modern Python package manager)
RUN pip install uv

WORKDIR /app

# Copy dependency files first for caching
COPY pyproject.toml ./
COPY poetry.lock ./

# Copy source code
COPY src/ ./src/

# Install dependencies (editable mode, src as top-level)
RUN uv pip install -e ./src

# Set PYTHONPATH so qmtl is importable
ENV PYTHONPATH="/app/src"

# Expose default port (change if needed)
EXPOSE 8000

# Set entrypoint (adjust as needed for your app)
CMD ["uvicorn", "qmtl.dag_manager.registry.api:app", "--host", "0.0.0.0", "--port", "8000"]
