FROM python:3.11-slim

RUN pip install uv

WORKDIR /app

COPY ../../pyproject.toml ./
COPY ../../requirements.txt ./
COPY ../../src/ ./src/

RUN uv pip install --system -e ./src

ENV PYTHONPATH="/app/src"

EXPOSE 9000

CMD ["python3", "-m", "qmtl.sdk"]
