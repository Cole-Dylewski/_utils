.PHONY: help install install-dev test test-cov lint format type-check security clean build

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Set up development environment (cross-platform)
	python setup-venv.py

install: ## Install package in development mode
	pip install -e .

install-dev: ## Install package with development dependencies
	pip install -e ".[dev]"
	pre-commit install

test: ## Run tests
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=_utils --cov-report=html --cov-report=term-missing

test-fast: ## Run only fast tests (skip slow/integration)
	pytest -m "not slow and not integration"

lint: ## Run linter
	ruff check .

lint-fix: ## Run linter and fix issues
	ruff check --fix .

format: ## Format code
	ruff format .

format-check: ## Check code formatting
	ruff format --check .

type-check: ## Run type checker
	mypy python/_utils

security: ## Run security checks
	bandit -r python/_utils
	safety check

quality: lint format-check type-check ## Run all quality checks

pre-commit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

clean: ## Clean build artifacts and cache
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

build: ## Build package
	python -m build

check-build: ## Check built package
	twine check dist/*

all: clean install-dev quality test ## Run all checks (clean, install, quality, test)

