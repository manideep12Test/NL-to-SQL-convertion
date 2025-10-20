# UV Development Environment Setup Script for Windows

Write-Host "🚀 Setting up AI Financial Query System with UV Package Manager" -ForegroundColor Cyan
Write-Host "==============================================================" -ForegroundColor Cyan

# Check if UV is installed
try {
    $uvVersion = uv --version
    Write-Host "✅ UV is already installed: $uvVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ UV is not installed. Installing UV..." -ForegroundColor Red
    
    # Install UV using the official installer
    try {
        Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
        Write-Host "✅ UV installed successfully" -ForegroundColor Green
        
        # Refresh PATH
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
    } catch {
        Write-Host "❌ Failed to install UV. Please install manually." -ForegroundColor Red
        Write-Host "Run: powershell -ExecutionPolicy ByPass -c `"irm https://astral.sh/uv/install.ps1 | iex`"" -ForegroundColor Yellow
        exit 1
    }
}

# Navigate to project directory
$projectPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectPath

Write-Host "📁 Working in directory: $((Get-Location).Path)" -ForegroundColor Blue

# Create virtual environment if it doesn't exist
if (-not (Test-Path ".venv")) {
    Write-Host "🔧 Creating virtual environment..." -ForegroundColor Yellow
    uv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✅ Virtual environment already exists" -ForegroundColor Green
}

# Install dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
uv sync
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Install development dependencies
Write-Host "🛠️  Installing development dependencies..." -ForegroundColor Yellow
uv sync --dev
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Development dependencies installation had issues, but continuing..." -ForegroundColor Yellow
}

# Verify installation
Write-Host "🔍 Verifying installation..." -ForegroundColor Yellow

try {
    uv run python -c "import streamlit; print('✅ Streamlit installed:', streamlit.__version__)"
    uv run python -c "import langchain; print('✅ LangChain installed:', langchain.__version__)"
    uv run python -c "import pandas; print('✅ Pandas installed:', pandas.__version__)"
} catch {
    Write-Host "❌ Some packages failed to import. Please check the installation." -ForegroundColor Red
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  Creating .env file template..." -ForegroundColor Yellow
    
    $envContent = @"
# Google API Key for Gemini AI
GOOGLE_API_KEY=your_google_api_key_here

# Database Configuration
DATABASE_PATH=code/src/data/banking.db

# Application Configuration
DEBUG=False
LOG_LEVEL=INFO
"@
    
    $envContent | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "📝 Please edit .env file and add your Google API key" -ForegroundColor Yellow
}

# Run initial tests to ensure everything works
Write-Host "🧪 Running initial tests..." -ForegroundColor Yellow

try {
    uv run python -c "import sys; sys.path.append('.'); from code.src.db import DatabaseManager; print('✅ Database module working')"
    uv run python -c "import sys; sys.path.append('.'); from code.src.agent import GeminiAgent; print('✅ Agent module working')"
    Write-Host "✅ Setup completed successfully!" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Some modules had import issues, but basic setup is complete." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 Setup Complete!" -ForegroundColor Cyan
Write-Host "==================" -ForegroundColor Cyan
Write-Host "To run the application:" -ForegroundColor White
Write-Host "  uv run streamlit run code/src/app.py" -ForegroundColor Green
Write-Host ""
Write-Host "To run with the main script:" -ForegroundColor White
Write-Host "  uv run code/src/main.py" -ForegroundColor Green
Write-Host ""
Write-Host "Development commands:" -ForegroundColor White
Write-Host "  uv run pytest                    # Run tests" -ForegroundColor Gray
Write-Host "  uv run black code/               # Format code" -ForegroundColor Gray
Write-Host "  uv run isort code/               # Sort imports" -ForegroundColor Gray
Write-Host "  uv run flake8 code/              # Lint code" -ForegroundColor Gray
Write-Host ""
Write-Host "Don't forget to:" -ForegroundColor Yellow
Write-Host "1. Add your Google API key to the .env file" -ForegroundColor Yellow
Write-Host "2. Check that the database file exists in code/src/data/" -ForegroundColor Yellow
Write-Host ""

# Pause to let user read the output
Write-Host "Press any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
