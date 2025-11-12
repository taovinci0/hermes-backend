.PHONY: install install-dev test format lint type-check clean run-paper run-backtest help

help:  ## Show this help message
	@echo "Hermes v1.0.0 - Weather→Markets Trading System"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install production dependencies
	uv pip install -e .

install-dev:  ## Install development dependencies
	uv pip install -e ".[dev]"

test:  ## Run test suite
	pytest -v

test-cov:  ## Run tests with coverage report
	pytest --cov=core --cov=agents --cov=venues --cov-report=html --cov-report=term

format:  ## Format code with black
	black core agents venues tests

lint:  ## Lint code with ruff
	ruff check core agents venues tests

lint-fix:  ## Fix linting issues automatically
	ruff check --fix core agents venues tests

type-check:  ## Run type checking with mypy
	mypy core agents venues

clean:  ## Clean up temporary files and caches
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov/ .coverage

setup:  ## Initial setup: copy env and install dependencies
	@if [ ! -f .env ]; then cp .env.sample .env; echo "Created .env file - please edit with your API keys"; fi
	$(MAKE) install-dev
	@echo ""
	@echo "Setup complete! Edit .env with your Zeus API key and run 'make help' for available commands."

run-fetch:  ## Fetch Zeus forecast (requires DATE and STATION env vars)
	python -m core.orchestrator --mode fetch --date $(DATE) --station $(STATION)

run-paper:  ## Run paper trading for active stations
	python -m core.orchestrator --mode paper --stations $(shell grep ACTIVE_STATIONS .env | cut -d= -f2)

run-backtest:  ## Run backtest (requires START, END, and STATIONS env vars)
	python -m core.orchestrator --mode backtest --start $(START) --end $(END) --stations $(STATIONS)

check: format lint type-check test  ## Run all checks (format, lint, type-check, test)

