# 🚀 Installation Guide

## Quick Installation (5 minutes)

### Prerequisites
- Python 3.9 or higher
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

### Option 1: Automated Setup (Recommended)

**Windows:**
```cmd
quick-start.bat
```

**Linux/Mac:**
```bash
chmod +x quick-start.sh
./quick-start.sh
```

### Option 2: Manual Setup

1. **Install Dependencies**
   ```bash
   # Using UV (recommended)
   uv sync
   
   # OR using pip
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit .env file and add your API key
   # GOOGLE_API_KEY=your_actual_api_key_here
   ```

3. **Run Application**
   ```bash
   cd code/src
   streamlit run app.py
   ```

4. **Access Application**
   Open your browser to: `http://localhost:8501`

## Troubleshooting

**Python Not Found:**
- Install Python from [python.org](https://python.org)
- Ensure Python is added to your PATH

**API Key Issues:**
- Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
- Ensure the key has access to Gemini models

**Dependencies Failed:**
- Try using a virtual environment:
  ```bash
  python -m venv .venv
  source .venv/bin/activate  # Linux/Mac
  .venv\Scripts\activate     # Windows
  pip install -r requirements.txt
  ```

## Need Help?
- 📖 See detailed documentation in [README.md](README.md)
- 🐛 Report issues on [GitHub Issues](https://github.com/eft-hackathon/hackathon1-ai_dev/issues)
- 💬 Check our [troubleshooting section](README.md#troubleshooting)
