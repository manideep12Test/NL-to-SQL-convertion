@echo off
REM Quick Start Script for AI-Powered Financial Query System (Windows)
REM This script helps you get the application running quickly

echo 🚀 AI-Powered Financial Query System - Quick Start
echo ==================================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.9+ first.
    pause
    exit /b 1
)

echo ✅ Python found
python --version

REM Check if we're in the right directory
if not exist "requirements.txt" (
    echo ❌ requirements.txt not found. Please run this script from the project root directory.
    pause
    exit /b 1
)

echo 📦 Installing dependencies...

REM Try UV first, fall back to pip
uv --version >nul 2>&1
if errorlevel 1 (
    echo 🔧 Using pip...
    pip install -r requirements.txt
) else (
    echo 🔧 Using UV package manager...
    uv sync
)

REM Check if .env file exists
if not exist ".env" (
    echo ⚠️  .env file not found. Copying from .env.example...
    if exist ".env.example" (
        copy ".env.example" ".env"
        echo 🔑 Please edit .env file and add your GOOGLE_API_KEY
    ) else (
        echo ❌ .env.example not found. Please create .env file manually.
    )
)

echo.
echo 🎉 Setup complete! To run the application:
echo 1. Edit .env file and add your Google API key
echo 2. Run: cd code\src ^&^& streamlit run app.py
echo 3. Open http://localhost:8501 in your browser
echo.
echo 📚 For detailed instructions, see README.md
echo.
pause
