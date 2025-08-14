.PHONY: help install test lint type-check build clean quality-check

help: ## Show this help message
	@echo "Interoperability Messaging Lab - Development Commands"
	@echo "=================================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "CLI Commands:"
	@echo "  interop-cli --help          Show CLI help"
	@echo "  interop-cli status          Show system status"
	@echo "  interop-cli interactive     Start interactive shell"
	@echo "  interop-cli api             Start REST API server"

install: ## Install package in development mode
	python3 -m pip install -e .

test: ## Run unit tests
	python3 -m pytest tests/ -v

lint: ## Run ruff linting
	python3 -m ruff check src/ tests/ cli.py

lint-fix: ## Run ruff linting with auto-fix
	python3 -m ruff check src/ tests/ cli.py --fix

type-check: ## Run mypy type checking
	mypy src/ --ignore-missing-imports

build: ## Build package distribution
	python3 -m build

clean: ## Clean build artifacts
	rm -rf build/ dist/ src/*.egg-info/ .pytest_cache/ .coverage htmlcov/

quality-check: ## Run all quality checks
	python3 scripts/quality_check.py

format: ## Format code with ruff
	ruff format src/ tests/ cli.py

check-all: lint type-check test build ## Run all checks (lint, type-check, test, build)

dev-setup: ## Set up development environment
	python3 -m pip install -e .
	python3 -m pip install ruff mypy types-jsonschema pytest pytest-cov

ci: ## Run CI checks (same as GitHub Actions)
	python3 -m pip install -e .
	python3 -m pip install pytest ruff mypy types-jsonschema
	pytest -q
	ruff check src/ tests/ cli.py
	mypy src/ --ignore-missing-imports
	python3 -m build
