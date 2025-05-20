.PHONY: venv install dev lint format test integration-test e2e-test coverage build clean run registry orchestrator docker-up docker-down ci

# Python 환경 설정
venv:
	uv venv create .venv

install:
	uv pip install -e .

dev:
	uv pip install -e ".[dev]"

# 코드 품질 관리
lint:
	uv pip install --system flake8 mypy
	flake8 src tests
	mypy src tests

format:
	uv pip install --system black isort
	black src tests
	isort src tests

# 테스트
# xfail 마크된 테스트는 반복 개발 시 제외 실행 (자동화)
test:
	python -m pytest tests/unit -k "not test_pipeline_execute and not test_pipeline_execute_with_inputs and not test_pipeline_execute_complex_dag" --html=tests/report/pytest_unit_report.html --self-contained-html

integration-test:
	python -m pytest tests/integration --html=tests/report/pytest_integration_report.html --self-contained-html

e2e-test:
	python -m pytest tests/e2e --html=tests/report/pytest_e2e_report.html --self-contained-html

coverage:
	python -m pytest --cov=src tests

# 빌드 관련
build:
	uv pip run build

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# 실행 관련
run:
	uvicorn src.qmtl.api:app --reload

registry:
	uvicorn src.qmtl.registry.api:app --reload --port 8000

orchestrator:
	uvicorn src.qmtl.orchestrator.api:app --reload --port 8080

# Docker 관련
docker-up:
	docker-compose -f docker-compose.dev.yml up -d

docker-down:
	docker-compose -f docker-compose.dev.yml down

ci: test integration-test

proto:
	bash scripts/generate_proto.sh