.PHONY: setup train predict test clean

# Setup virtual environment and install dependencies
setup:
	python -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

# Train the model
train:
	.venv/bin/python -m mizan_cli.train --comps data/raw/comps.csv

# Train with HistGradientBoosting
train-hgb:
	.venv/bin/python -m mizan_cli.train --comps data/raw/comps.csv --model-type hgb

# Run prediction
predict:
	.venv/bin/python -m mizan_cli.predict --input data/raw/subject_properties.csv

# Run tests
test:
	.venv/bin/pytest tests/ -v

# Run tests with coverage
test-cov:
	.venv/bin/pytest tests/ --cov=src --cov-report=html

# Clean generated files
clean:
	rm -rf .venv __pycache__ .pytest_cache
	rm -rf models/*.joblib models/*.parquet
	rm -rf reports/*
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Format code
format:
	.venv/bin/black src tests
	.venv/bin/ruff check src tests --fix

# Lint code
lint:
	.venv/bin/ruff check src tests
