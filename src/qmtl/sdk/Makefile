run:
	uv venv .venv && source .venv/bin/activate && uv pip install -r requirements.txt || true && python3 -m qmtl.sdk

test:
	pytest

build:
	docker build -t qmtl-sdk .
