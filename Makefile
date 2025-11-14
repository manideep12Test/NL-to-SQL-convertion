# Makefile for AI-Powered Financial Query System

.PHONY: help install run test clean dev setup

# Default target
help:
	@echo "🚀 AI-Powered Financial Query System"
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make setup      - Complete setup (install + env)"
	@echo "  make run        - Run the application"
	@echo "  make dev        - Install dev dependencies"
	@echo "  make test       - Run tests"
	@echo "  make clean      - Clean up temporary files"
	@echo "  make help       - Show this help message"

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	@if command -v uv >/dev/null 2>&1; then \
		echo "🔧 Using UV package manager..."; \
		uv sync; \
	else \
		echo "🔧 Using pip..."; \
		pip install -r requirements.txt; \
	fi

# Complete setup
setup: install
	@echo "⚙️ Setting up environment..."
	@if [ ! -f .env ]; then \
		if [ -f .env.example ]; then \
			cp .env.example .env; \
			echo "📝 Created .env from .env.example"; \
			echo "🔑 Please edit .env and add your GOOGLE_API_KEY"; \
		else \
			echo "❌ .env.example not found"; \
		fi; \
	else \
		echo "✅ .env file already exists"; \
	fi

# Run the application
run:
	@echo "🚀 Starting AI-Powered Financial Query System..."
	@cd code/src && streamlit run app.py

# Install development dependencies
dev:
	@echo "🛠️ Installing development dependencies..."
	@if command -v uv >/dev/null 2>&1; then \
		uv sync --group dev; \
	else \
		pip install -r requirements.txt pytest black isort flake8; \
	fi

# Run tests
test:
	@echo "🧪 Running tests..."
	@cd code/src && python -m pytest tests/

# Clean up
clean:
	@echo "🧹 Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*.pyd" -delete
	@find . -type f -name ".coverage" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} +

# Check if environment is set up
check-env:
	@if [ ! -f .env ]; then \
		echo "❌ .env file not found. Run 'make setup' first."; \
		exit 1; \
	fi
	@if ! grep -q "GOOGLE_API_KEY=" .env || grep -q "your_api_key_here" .env; then \
		echo "❌ Please set your GOOGLE_API_KEY in .env file"; \
		exit 1; \
	fi
	@echo "✅ Environment is properly configured"
