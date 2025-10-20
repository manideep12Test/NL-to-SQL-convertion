#!/bin/bash
# Quick Start Script for AI-Powered Financial Query System
# This script helps you get the application running quickly

echo "🚀 AI-Powered Financial Query System - Quick Start"
echo "=================================================="

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.9+ first."
    exit 1
fi

echo "✅ Python found: $(python --version)"

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found. Please run this script from the project root directory."
    exit 1
fi

echo "📦 Installing dependencies..."

# Try UV first, fall back to pip
if command -v uv &> /dev/null; then
    echo "🔧 Using UV package manager..."
    uv sync
else
    echo "🔧 Using pip..."
    pip install -r requirements.txt
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "🔑 Please edit .env file and add your GOOGLE_API_KEY"
    else
        echo "❌ .env.example not found. Please create .env file manually."
    fi
fi

echo ""
echo "🎉 Setup complete! To run the application:"
echo "1. Edit .env file and add your Google API key"
echo "2. Run: cd code/src && streamlit run app.py"
echo "3. Open http://localhost:8501 in your browser"
echo ""
echo "📚 For detailed instructions, see README.md"
