#!/bin/bash

# Financial Corpus Analyzer - Startup Script

echo "🚀 Starting Financial Corpus Analyzer..."
echo ""

# Check if we're in the right directory
if [ ! -f "src/ui/server.py" ]; then
    echo "❌ Error: This script must be run from the universal-orchestrator directory"
    echo "   Run: cd universal-orchestrator && ./start.sh"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from .env.example..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your API keys!"
    echo "   Required: OPENAI_API_KEY or ANTHROPIC_API_KEY or GOOGLE_API_KEY"
    echo ""
    read -p "Press Enter to continue once you've added your API keys..."
fi

# Start the server
echo ""
echo "✨ Starting Financial Corpus Analyzer on http://localhost:8000"
echo ""
echo "Features available:"
echo "  📁 Drag & drop file upload (PDF, CSV, XLSX, DOC, TXT)"
echo "  🔗 URL scraping for financial data"
echo "  💎 Alpha extraction with AI"
echo "  📊 Comprehensive report generation"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python -m src.ui.server
