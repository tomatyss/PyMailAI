# PyMailAI Makefile

.PHONY: help install install-hooks test test-cov format lint type-check clean build deploy

help:
	@echo "Available commands:"
	@echo "  make install      Install development dependencies"
	@echo "  make install-hooks Install pre-commit hooks"
	@echo "  make test        Run tests"
	@echo "  make test-cov    Run tests with coverage report"
	@echo "  make format      Format code with black and isort"
	@echo "  make lint        Run linting checks"
	@echo "  make type-check  Run type checking"
	@echo "  make clean       Remove build artifacts"
	@echo "  make build       Build distribution packages"
	@echo "  make deploy      Upload to PyPI (requires PyPI token)"

install:
	pip install -e ".[dev]"
	pre-commit install

install-hooks:
	pre-commit install

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=pymailai --cov-report=term-missing

format:
	black src/ tests/ examples/
	isort src/ tests/ examples/

lint:
	black --check src/ tests/ examples/
	isort --check-only src/ tests/ examples/
	flake8 src/ tests/ examples/

type-check:
	mypy src/ tests/ examples/

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf .mypy_cache
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -r {} +

build: clean
	python -m build

deploy: build
	python -m twine upload dist/*
