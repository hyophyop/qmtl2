# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Install uv (modern Python package manager)
RUN pip install uv

WORKDIR /app

# Copy only dependency files first for caching
COPY pyproject.toml ./
COPY poetry.lock ./

# Install dependencies (editable mode)
RUN uv pip install -e .

# Copy source code
COPY src/ ./src/

# Expose default port (change if needed)
EXPOSE 8000

# Set entrypoint (adjust as needed for your app)
CMD ["uvicorn", "qmtl.gateway.api:app", "--host", "0.0.0.0", "--port", "8000"]
