# 🚀 Setup Instructions & Installation Guide

## AI-Powered Financial Query System - Complete Setup Documentation

### 📋 Table of Contents
- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Installation Methods](#installation-methods)
- [Configuration Guide](#configuration-guide)
- [Environment Setup](#environment-setup)
- [Testing Installation](#testing-installation)
- [Troubleshooting](#troubleshooting)
- [Advanced Setup](#advanced-setup)

---

## ⚡ Quick Start

### One-Command Setup (Recommended)

**Windows (PowerShell):**
```powershell
.\setup_uv.ps1
```

**macOS/Linux (Bash):**
```bash
./setup_uv.sh
```

**Estimated Time:** 5-10 minutes  
**What it does:** Installs UV, sets up environment, configures dependencies, and runs verification tests

---

## 📋 Prerequisites

### System Requirements

#### Minimum Requirements
- **Operating System**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 18.04+)
- **Python**: Version 3.9 or higher
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 2GB free space
- **Network**: Internet connection for package downloads

#### Required Software
- **Git**: For cloning the repository
- **Web Browser**: Chrome, Firefox, Safari, or Edge (for Streamlit interface)
- **Terminal/Command Line**: PowerShell (Windows), Terminal (macOS/Linux)

#### API Requirements
- **Google Gemini API Key**: Required for AI functionality
  - Get your key at: [Google AI Studio](https://makersuite.google.com/app/apikey)
  - Free tier available with generous limits

### Hardware Recommendations
- **Development**: 8GB RAM, SSD storage
- **Production**: 16GB RAM, multi-core CPU
- **Heavy Analysis**: 32GB RAM for large datasets

---

## 🔧 Installation Methods

### Method 1: Automated Setup (Recommended)

#### Windows Setup
```powershell
# 1. Clone the repository
git clone https://github.com/eft-hackathon/hackathon1-ai_dev.git
cd hackathon1-ai_dev

# 2. Run automated setup
.\setup_uv.ps1

# 3. Activate environment and start
uv run streamlit run code/src/app.py
```

#### Unix/Linux/macOS Setup
```bash
# 1. Clone the repository
git clone https://github.com/eft-hackathon/hackathon1-ai_dev.git
cd hackathon1-ai_dev

# 2. Make script executable and run
chmod +x setup_uv.sh
./setup_uv.sh

# 3. Activate environment and start
uv run streamlit run code/src/app.py
```

### Method 2: Manual UV Installation

#### Step 1: Install UV Package Manager
```bash
# Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Step 2: Setup Project
```bash
# Clone repository
git clone https://github.com/eft-hackathon/hackathon1-ai_dev.git
cd hackathon1-ai_dev

# Install dependencies
uv sync

# Verify installation
uv run python --version
```

### Method 3: Traditional Python Setup

#### Using Virtual Environment
```bash
# Create virtual environment
python -m venv ai_query_env

# Activate environment
# Windows:
ai_query_env\Scripts\activate
# macOS/Linux:
source ai_query_env/bin/activate

# Install dependencies
pip install -r code/requirements.txt

# Install package in development mode
pip install -e .
```

### Method 4: Docker Setup (Advanced)

```dockerfile
# Dockerfile example (create in project root)
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install uv
RUN uv sync

EXPOSE 8501

CMD ["uv", "run", "streamlit", "run", "code/src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
# Build and run container
docker build -t ai-financial-query .
docker run -p 8501:8501 ai-financial-query
```

---

## ⚙️ Configuration Guide

### Environment Variables

#### Required Configuration
Create a `.env` file in the project root:

```bash
# Copy example file
cp .env.example .env

# Edit with your values
GOOGLE_API_KEY=your_gemini_api_key_here
DATABASE_URL=code/src/data/banking.db
LOG_LEVEL=INFO
STREAMLIT_PORT=8501
```

#### Environment Variables Reference
```bash
# API Configuration
GOOGLE_API_KEY=your_api_key          # Required: Gemini API key
GEMINI_MODEL=gemini-1.5-flash        # Optional: Model version

# Database Configuration
DATABASE_URL=code/src/data/banking.db  # Required: Database path
DB_TIMEOUT=30                          # Optional: Query timeout (seconds)

# Application Configuration
STREAMLIT_PORT=8501                    # Optional: Web interface port
LOG_LEVEL=INFO                         # Optional: DEBUG, INFO, WARNING, ERROR
MAX_QUERY_RESULTS=1000                 # Optional: Result limit

# Development Configuration
DEBUG_MODE=false                       # Optional: Enable debug features
CACHE_ENABLED=true                     # Optional: Enable query caching
```

### API Key Setup

#### Getting Your Gemini API Key
1. **Visit Google AI Studio**: https://makersuite.google.com/app/apikey
2. **Sign in** with your Google account
3. **Create API Key** - click "Create API Key"
4. **Copy the key** - save it securely
5. **Add to .env file** - paste in GOOGLE_API_KEY field

#### API Key Security Best Practices
```bash
# ✅ Good: Use environment variables
export GOOGLE_API_KEY="your_key_here"

# ❌ Bad: Hardcode in source files
api_key = "AIzaSy..."  # Never do this!

# ✅ Good: Use .env files (not committed to git)
echo "GOOGLE_API_KEY=your_key" >> .env

# ✅ Good: Use system keychain/vault in production
```

### Database Configuration

#### Default Database Setup
The system includes a pre-built SQLite database with sample banking data:

```bash
# Database location
code/src/data/banking.db

# Backup location (if needed)
code/src/data/banking_backup.db

# Schema definition
code/src/data/banking_schema_sqlite.sql
```

#### Custom Database Setup
```python
# For custom database, update DatabaseManager configuration
from code.src.data.database_manager import DatabaseManager

# Initialize with custom database
db = DatabaseManager("path/to/your/database.db")

# Verify connection
if db.test_connection():
    print("✅ Database connected successfully")
```

---

## 🌍 Environment Setup

### Development Environment

#### VS Code Setup (Recommended)
```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["code/src/tests"]
}
```

#### Recommended Extensions
- Python (Microsoft)
- Pylance (Microsoft)
- GitLens
- Thunder Client (for API testing)
- SQLite Viewer

#### PyCharm Setup
```python
# Configure interpreter
# File → Settings → Project → Python Interpreter
# Add New → UV Environment → Point to project directory

# Configure run configuration
# Run → Edit Configurations → Add New → Python
# Script path: code/src/app.py
# Parameters: streamlit run
```

### Production Environment

#### Environment Optimization
```bash
# Production environment setup
export ENVIRONMENT=production
export DEBUG_MODE=false
export LOG_LEVEL=WARNING
export CACHE_ENABLED=true

# Performance tuning
export STREAMLIT_SERVER_MAX_UPLOAD_SIZE=200
export STREAMLIT_SERVER_ENABLE_CORS=false
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

#### Security Configuration
```bash
# Secure API key management
export GOOGLE_API_KEY_FILE="/secure/path/to/key.txt"

# Database security
export DB_ENCRYPTION_KEY="your_encryption_key"
export DB_BACKUP_LOCATION="/secure/backups/"

# Network security
export ALLOWED_HOSTS="localhost,yourdomain.com"
export SSL_REQUIRED=true
```

---

## 🧪 Testing Installation

### Verification Steps

#### 1. Quick Health Check
```bash
# Test UV installation
uv --version

# Test Python environment
uv run python --version

# Test dependencies
uv run python -c "import streamlit, google.generativeai, pandas, plotly; print('✅ All imports successful')"
```

#### 2. Database Verification
```bash
# Run database test
uv run python code/src/test_db_direct.py

# Expected output:
# ✅ Database connection successful
# ✅ All tables present
# ✅ Sample data loaded
```

#### 3. API Connection Test
```bash
# Test Gemini API connection
uv run python -c "
from code.src.Agent.gemini_agent import GeminiAgent
agent = GeminiAgent()
print('✅ API connection successful')
"
```

#### 4. Full Application Test
```bash
# Start the application
uv run streamlit run code/src/app.py

# Test in browser
# Navigate to: http://localhost:8501
# Try sample query: "Show me the top 5 customers by account balance"
```

### Automated Test Suite

#### Run Complete Test Suite
```bash
# Run all tests
uv run python -m pytest code/src/tests/ -v

# Run specific test categories
uv run python -m pytest code/src/tests/unit/ -v          # Unit tests
uv run python -m pytest code/src/tests/integration/ -v   # Integration tests
uv run python -m pytest code/src/tests/e2e/ -v          # End-to-end tests

# Generate coverage report
uv run python -m pytest --cov=code/src --cov-report=html
```

#### Test Results Interpretation
```bash
# ✅ Success indicators
collected 45 items
code/src/tests/test_database.py::test_connection PASSED
code/src/tests/test_gemini_agent.py::test_query_generation PASSED
...
====================== 45 passed in 23.5s ======================

# ❌ Failure indicators
FAILED code/src/tests/test_api.py::test_invalid_key - AssertionError
# Check API key configuration

# ⚠️ Warning indicators
code/src/app.py::test_streamlit - warnings.warn
# Non-critical warnings, application should still work
```

---

## 🔧 Troubleshooting

### Common Issues & Solutions

#### 1. UV Installation Problems

**Issue**: `uv: command not found`
```bash
# Solution 1: Restart terminal after installation
# Close and reopen your terminal

# Solution 2: Manually add to PATH (Linux/macOS)
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Solution 3: Alternative installation method
pip install uv
```

**Issue**: `Permission denied during installation`
```bash
# Windows: Run PowerShell as Administrator
# macOS/Linux: Use proper permissions
sudo curl -LsSf https://astral.sh/uv/install.sh | sh

# Or install to user directory
curl -LsSf https://astral.sh/uv/install.sh | sh -s -- --install-dir ~/.local/bin
```

#### 2. Python Version Issues

**Issue**: `Python 3.9+ required`
```bash
# Check current version
python --version

# Install Python 3.9+ using UV
uv python install 3.11

# Use specific Python version
uv python pin 3.11
```

**Issue**: Multiple Python versions causing conflicts
```bash
# Use specific Python with UV
uv venv --python 3.11

# Verify correct version
uv run python --version
```

#### 3. API Key Configuration Issues

**Issue**: `🔑 API key issue detected` when clicking Execute Query
This is the most common error users face. Here are step-by-step solutions:

**Solution 1: Check API Key Existence**
```bash
# Check if .env file exists in project root
ls -la .env

# If missing, create it:
cp .env.example .env

# Verify API key is set (should show your key, not "None")
# Windows:
type .env | findstr GOOGLE_API_KEY
# Linux/macOS:
grep GOOGLE_API_KEY .env
```

**Solution 2: Verify API Key Format**
```bash
# API key should start with "AIza" and be about 39 characters long
# ✅ Correct format: GOOGLE_API_KEY=AIzaSyB1234567890abcdefghijklmnopqrstuvwxyz
# ❌ Wrong format: GOOGLE_API_KEY=your_key_here

# Test key format
echo $GOOGLE_API_KEY | grep -E "^AIza[A-Za-z0-9_-]{35}$"  # Linux/macOS
```

**Solution 3: Get New API Key**
If you don't have an API key or it's invalid:
1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the entire key (starts with AIza...)
5. Add to .env file: `GOOGLE_API_KEY=your_copied_key`

**Solution 4: Fix .env File Format**
```bash
# Common .env file mistakes:

# ❌ WRONG - spaces around equals
GOOGLE_API_KEY = AIzaSy...

# ❌ WRONG - quotes around key
GOOGLE_API_KEY="AIzaSy..."

# ❌ WRONG - missing key
GOOGLE_API_KEY=

# ✅ CORRECT format
GOOGLE_API_KEY=AIzaSyB1234567890abcdefghijklmnopqrstuvwxyz
```

**Solution 5: Test API Key Validity**
```bash
# Test API key directly with curl
curl -H "x-goog-api-key: YOUR_API_KEY_HERE" \
  https://generativelanguage.googleapis.com/v1/models

# Expected response: JSON with model list
# Error response means invalid key
```

**Solution 6: Environment Variable Loading**
```bash
# Test if environment variables are loading correctly
uv run python -c "
import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv('GOOGLE_API_KEY')
print(f'API Key loaded: {api_key[:10]}...' if api_key else 'API Key: None')
"

# Should show: API Key loaded: AIzaSyB123...
# If shows "None", .env file isn't being read
```

**Solution 7: Restart Application**
After fixing .env file:
```bash
# Stop Streamlit (Ctrl+C in terminal)
# Then restart:
uv run streamlit run code/src/app.py
```

**Issue**: `Invalid API key` or `Authentication failed`
```bash
# Verify API key format
echo $GOOGLE_API_KEY | grep "AIza"  # Should start with AIza

# Test API key directly
curl -H "x-goog-api-key: $GOOGLE_API_KEY" \
  https://generativelanguage.googleapis.com/v1/models

# Regenerate API key if needed
# Visit: https://makersuite.google.com/app/apikey
```

**Issue**: `.env file not loading`
```bash
# Verify .env file location (should be in project root)
ls -la .env

# Check .env file format (no spaces around =)
# ✅ Correct: GOOGLE_API_KEY=your_key_here
# ❌ Wrong:   GOOGLE_API_KEY = your_key_here

# Test environment loading
uv run python -c "import os; print(os.getenv('GOOGLE_API_KEY'))"
```

#### 4. Database Issues

**Issue**: `Database not found` or `Permission denied`
```bash
# Verify database exists
ls -la code/src/data/banking.db

# Check permissions
chmod 644 code/src/data/banking.db

# Regenerate database if corrupted
uv run python code/src/data/database_manager.py
```

**Issue**: `Database locked` error
```bash
# Check for other connections
lsof code/src/data/banking.db  # Linux/macOS
# Kill any hanging processes

# Reset database connection
uv run python -c "
from code.src.data.database_manager import DatabaseManager
db = DatabaseManager()
db.close_connection()
"
```

#### 5. Streamlit Issues

**Issue**: `Port already in use`
```bash
# Find process using port 8501
netstat -tulpn | grep 8501  # Linux
netstat -an | findstr 8501  # Windows

# Kill process
kill -9 <PID>  # Linux/macOS
taskkill /PID <PID> /F  # Windows

# Or use different port
uv run streamlit run code/src/app.py --server.port 8502
```

**Issue**: `Module not found` errors in Streamlit
```bash
# Verify PYTHONPATH
uv run python -c "import sys; print(sys.path)"

# Run from correct directory
cd hackathon1-ai_dev
uv run streamlit run code/src/app.py

# Install in development mode
uv pip install -e .
```

#### 6. Memory/Performance Issues

**Issue**: High memory usage or slow performance
```bash
# Monitor memory usage
uv run python -c "
import psutil
print(f'Memory: {psutil.virtual_memory().percent}%')
print(f'CPU: {psutil.cpu_percent()}%')
"

# Optimize for large datasets
export MAX_QUERY_RESULTS=100
export CACHE_ENABLED=true

# Use streaming for large results
uv run streamlit run code/src/app.py --server.maxUploadSize 50
```

### Platform-Specific Issues

#### Windows-Specific
```powershell
# PowerShell execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Long path support
git config --global core.longpaths true

# Antivirus interference
# Add project folder to antivirus exclusions
```

#### macOS-Specific
```bash
# Xcode Command Line Tools
xcode-select --install

# Homebrew conflicts
brew doctor

# Python from system vs. Homebrew
which python3
/usr/bin/python3 --version
```

#### Linux-Specific
```bash
# Missing system dependencies
sudo apt-get update
sudo apt-get install python3-dev python3-pip build-essential

# SQLite development headers
sudo apt-get install libsqlite3-dev

# SSL certificates
sudo apt-get install ca-certificates
```

---

## 🚀 Advanced Setup

### Development Workflow

#### Git Configuration
```bash
# Configure git hooks
cp .githooks/pre-commit .git/hooks/
chmod +x .git/hooks/pre-commit

# Configure branch protection
git config branch.main.protected true

# Set up conventional commits
npm install -g @commitlint/cli @commitlint/config-conventional
```

#### Code Quality Tools
```bash
# Install development dependencies
uv add --dev black pylint mypy pytest pytest-cov

# Configure pre-commit hooks
uv add --dev pre-commit
uv run pre-commit install

# Run quality checks
uv run black code/src/           # Code formatting
uv run pylint code/src/          # Linting
uv run mypy code/src/            # Type checking
```

### Performance Optimization

#### Database Optimization
```sql
-- Add indices for common queries
CREATE INDEX idx_customer_balance ON accounts(customer_id, balance);
CREATE INDEX idx_transaction_date ON transactions(transaction_date);
CREATE INDEX idx_account_type ON accounts(account_type);
```

#### Caching Configuration
```python
# Streamlit caching optimization
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_database_schema():
    return DatabaseManager().get_schema_info()

@st.cache_resource
def initialize_ai_agent():
    return GeminiAgent()
```

#### Memory Management
```bash
# Production environment tuning
export STREAMLIT_SERVER_MAX_UPLOAD_SIZE=200
export STREAMLIT_SERVER_ENABLE_CORS=false
export PYTHON_GC_GENERATION1_THRESHOLD=700
export PYTHON_GC_GENERATION2_THRESHOLD=10
```

### Deployment Options

#### Local Production Deployment
```bash
# Install production WSGI server
uv add gunicorn

# Create production configuration
# gunicorn_config.py
bind = "0.0.0.0:8501"
workers = 2
worker_class = "sync"
timeout = 120
max_requests = 1000
```

#### Docker Production Setup
```dockerfile
# Multi-stage production Dockerfile
FROM python:3.11-slim as builder
WORKDIR /app
COPY . .
RUN pip install uv && uv sync --no-dev

FROM python:3.11-slim as runtime
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/code /app/code
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8501
CMD ["streamlit", "run", "code/src/app.py"]
```

#### Cloud Deployment Options
```yaml
# Heroku deployment (Procfile)
web: streamlit run code/src/app.py --server.port=$PORT --server.address=0.0.0.0

# Railway deployment
railway login
railway init
railway add
railway up

# Google Cloud Run
gcloud run deploy ai-financial-query \
  --source . \
  --port 8501 \
  --allow-unauthenticated
```

---

## 📊 Setup Verification Checklist

### ✅ Pre-Installation Checklist
- [ ] Python 3.9+ installed and accessible
- [ ] Git installed and configured
- [ ] Google Gemini API key obtained
- [ ] 2GB+ free disk space available
- [ ] Internet connection active

### ✅ Installation Verification
- [ ] UV package manager installed (`uv --version`)
- [ ] Project dependencies installed (`uv sync` completed)
- [ ] Environment variables configured (`.env` file created)
- [ ] Database accessible (`test_db_direct.py` passes)
- [ ] API connection working (Gemini agent initializes)

### ✅ Application Testing
- [ ] Streamlit application starts (`streamlit run` works)
- [ ] Web interface loads at http://localhost:8501
- [ ] Sample query executes successfully
- [ ] Data visualization renders correctly
- [ ] No error messages in console

### ✅ Development Environment
- [ ] IDE/editor configured with Python interpreter
- [ ] Git repository properly initialized
- [ ] Code formatting tools available
- [ ] Test suite runs successfully (`pytest` passes)
- [ ] Documentation accessible

### ✅ Production Readiness (Optional)
- [ ] Security configurations applied
- [ ] Performance optimizations enabled
- [ ] Monitoring and logging configured
- [ ] Backup procedures established
- [ ] Deployment pipeline tested

---

## 🆘 Getting Help

### Self-Help Resources
1. **Check this documentation first** - Most issues are covered here
2. **Review error messages carefully** - They often contain the solution
3. **Test with sample queries** - Use provided examples to isolate issues
4. **Check system requirements** - Ensure your system meets prerequisites

### Community Support
- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share experiences
- **Wiki**: Community-contributed tips and tricks

### Professional Support
- **Enterprise Support**: Available for business users
- **Custom Development**: Tailored solutions and integrations
- **Training Services**: Team onboarding and best practices

### Emergency Recovery
```bash
# Complete reset (use with caution)
rm -rf .venv/
rm uv.lock
uv sync

# Database reset
rm code/src/data/banking.db
uv run python code/src/data/database_manager.py

# Configuration reset
rm .env
cp .env.example .env
# Edit .env with your values
```

---

*This setup guide provides comprehensive instructions for all installation scenarios and common troubleshooting situations. For additional help, please refer to the community resources or contact support.*
