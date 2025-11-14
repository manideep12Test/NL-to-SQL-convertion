#!/bin/bash
# UV Development Environment Setup Script

set -e

echo "🚀 Setting up AI Financial Query System with UV Package Manager"
echo "=============================================================="

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo "❌ UV is not installed. Installing UV..."
    
    # Detect OS and install UV accordingly
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        echo "Detected Windows. Please run the following command in PowerShell:"
        echo "powershell -ExecutionPolicy ByPass -c \"irm https://astral.sh/uv/install.ps1 | iex\""
        exit 1
    else
        # Unix-like systems
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
    fi
else
    echo "✅ UV is already installed: $(uv --version)"
fi

# Navigate to project directory
cd "$(dirname "$0")"

echo "📁 Working in directory: $(pwd)"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "🔧 Creating virtual environment..."
    uv venv
else
    echo "✅ Virtual environment already exists"
fi

# Install dependencies
echo "📦 Installing dependencies..."
uv sync

# Install development dependencies
echo "🛠️  Installing development dependencies..."
uv sync --dev

# Verify installation
echo "🔍 Verifying installation..."
uv run python -c "import streamlit; print('✅ Streamlit installed:', streamlit.__version__)"
uv run python -c "import langchain; print('✅ LangChain installed:', langchain.__version__)"
uv run python -c "import pandas; print('✅ Pandas installed:', pandas.__version__)"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Creating .env file template..."
    cat > .env << EOF
# Google API Key for Gemini AI
GOOGLE_API_KEY=your_google_api_key_here

# Database Configuration
DATABASE_PATH=code/src/data/banking.db

# Application Configuration
DEBUG=False
LOG_LEVEL=INFO
EOF
    echo "📝 Please edit .env file and add your Google API key"
fi

# Run initial tests to ensure everything works
echo "🧪 Running initial tests..."
if uv run python -c "from code.src.app import *; print('✅ Application imports working')"; then
    echo "✅ Setup completed successfully!"
else
    echo "❌ There were some issues with the setup. Please check the error messages above."
    exit 1
fi

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo "To run the application:"
echo "  uv run streamlit run code/src/app.py"
echo ""
echo "To run with the main script:"
echo "  uv run code/src/main.py"
echo ""
echo "Development commands:"
echo "  uv run pytest                    # Run tests"
echo "  uv run black code/               # Format code"
echo "  uv run isort code/               # Sort imports"
echo "  uv run flake8 code/              # Lint code"
echo ""
echo "Don't forget to:"
echo "1. Add your Google API key to the .env file"
echo "2. Check that the database file exists in code/src/data/"
echo ""
