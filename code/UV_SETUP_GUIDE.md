# UV Installation and Setup Guide

## Prerequisites
- Python 3.9 or higher
- Windows PowerShell (for Windows users)

## 1. Install UV Package Manager

### Windows (PowerShell)
```powershell
# Install UV using the official installer
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Alternative: Install via pip
```bash
pip install uv
```

## 2. Verify Installation
```bash
uv --version
```

## 3. Project Setup with UV

### Initialize the project (if starting fresh)
```bash
cd "c:\Users\PC\Prince works\hackathon1-ai_dev"
uv init --name ai-financial-query-system
```

### Install dependencies
```bash
# Install all dependencies
uv sync

# Install with development dependencies
uv sync --dev

# Install only production dependencies
uv sync --no-dev
```

### Alternative: Install from requirements.txt (migration)
```bash
# If migrating from pip/requirements.txt
uv pip install -r code/requirements.txt
```

## 4. Running the Application

### Method 1: Using UV directly
```bash
# Run the main application
uv run code/src/main.py

# Or run streamlit directly
uv run streamlit run code/src/app.py
```

### Method 2: Using the installed script
```bash
# After installation, you can use the script
uv run ai-query
```

## 5. Development Workflow

### Add new dependencies
```bash
# Add a new package
uv add package-name

# Add development dependency
uv add --dev pytest

# Add with version constraints
uv add "pandas>=2.0.0,<3.0.0"
```

### Remove dependencies
```bash
uv remove package-name
```

### Update dependencies
```bash
# Update all packages
uv lock --upgrade

# Update specific package
uv add package-name --upgrade
```

### Create virtual environment
```bash
# UV automatically manages virtual environments
# But you can create one explicitly if needed
uv venv

# Activate it (Windows)
.venv\Scripts\activate

# Activate it (Unix/MacOS)
source .venv/bin/activate
```

## 6. Development Tools

### Code formatting
```bash
# Format code with black
uv run black code/

# Sort imports with isort
uv run isort code/

# Run type checking
uv run mypy code/
```

### Testing
```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=code --cov-report=html
```

### Linting
```bash
# Run flake8
uv run flake8 code/
```

## 7. Environment Management

### List environments
```bash
uv venv list
```

### Remove environment
```bash
uv venv remove .venv
```

### Python version management
```bash
# List available Python versions
uv python list

# Install specific Python version
uv python install 3.11

# Use specific Python version
uv python pin 3.11
```

## 8. Project Build and Distribution

### Build the project
```bash
uv build
```

### Install in editable mode (for development)
```bash
uv pip install -e .
```

## 9. Migration from pip/virtualenv

### Step 1: Generate uv.lock from requirements.txt
```bash
uv pip compile code/requirements.txt -o uv.lock
```

### Step 2: Sync dependencies
```bash
uv sync
```

### Step 3: Test the application
```bash
uv run streamlit run code/src/app.py
```

## 10. Performance Benefits

UV provides several advantages over traditional pip:

- **Speed**: 10-100x faster than pip for package installation
- **Reliability**: Better dependency resolution and conflict detection
- **Reproducibility**: Lock files ensure consistent environments
- **Cross-platform**: Works consistently across Windows, macOS, and Linux

## 11. Common Commands Summary

```bash
# Essential commands
uv sync                    # Install dependencies
uv add package            # Add new dependency
uv remove package         # Remove dependency
uv run command           # Run command in project environment
uv build                 # Build the project
uv lock                  # Update lock file

# Development
uv sync --dev           # Install with dev dependencies
uv run pytest          # Run tests
uv run black .          # Format code
uv run streamlit run code/src/app.py  # Run the app
```

## 12. Environment Variables

Make sure to set up your environment variables in `.env` file:

```env
GOOGLE_API_KEY=your_google_api_key_here
```

## Troubleshooting

### Common Issues:

1. **UV not found**: Make sure UV is in your PATH after installation
2. **Permission errors**: Run PowerShell as Administrator on Windows
3. **Python version conflicts**: Use `uv python pin` to set project Python version
4. **Dependency conflicts**: Use `uv lock --upgrade` to resolve conflicts

### Getting Help:
```bash
uv --help
uv add --help
uv sync --help
```
