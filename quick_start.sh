#!/bin/bash

# Quick start script for the Geopolitical Intelligence System

echo "🌍 Geopolitical Intelligence System - Quick Start"
echo "=================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup.py first:"
    echo "   python setup.py"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
if [ "$OS" = "Windows_NT" ]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "Please edit .env file with your API keys before continuing."
    exit 1
fi

echo "✅ Environment activated"

# Show menu
echo ""
echo "What would you like to do?"
echo "1. Collect news data"
echo "2. Process collected articles"
echo "3. Generate daily report"
echo "4. Generate weekly report"
echo "5. Run full pipeline"
echo "6. Show system status"
echo "7. Start dashboard"
echo "8. Start chatbot"
echo "9. Run scheduled tasks"
echo "0. Exit"

read -p "Enter your choice (0-9): " choice

case $choice in
    1)
        echo "🔍 Collecting news data..."
        python main.py --collect
        ;;
    2)
        echo "🧠 Processing articles with NLP..."
        python main.py --process
        ;;
    3)
        echo "📊 Generating daily report..."
        python main.py --report daily
        ;;
    4)
        echo "📊 Generating weekly report..."
        python main.py --report weekly
        ;;
    5)
        echo "🚀 Running full pipeline..."
        python main.py --full-pipeline
        ;;
    6)
        echo "📈 Showing system status..."
        python main.py --status
        ;;
    7)
        echo "🌐 Starting dashboard..."
        echo "Dashboard will be available at: http://localhost:5000"
        python src/dashboard/app.py
        ;;
    8)
        echo "🤖 Starting chatbot..."
        echo "Chatbot will be available at: http://localhost:7860"
        python src/chatbot/chatbot_app.py
        ;;
    9)
        echo "⏰ Starting scheduled tasks..."
        echo "Press Ctrl+C to stop"
        python main.py --schedule
        ;;
    0)
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo "❌ Invalid choice. Please try again."
        exit 1
        ;;
esac
