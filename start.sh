#!/bin/bash
# Quick start script for Remote Camera System

echo "🚀 Remote Camera System - Quick Start"
echo "===================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Set environment variables
export PORT=5000
export PYTHONUNBUFFERED=1

# Create logs directory
mkdir -p logs

echo "🌐 Starting Remote Camera System..."
echo "📱 Access URL: http://localhost:5000"
echo "👤 Admin Panel: http://localhost:5000"
echo "===================================="

# Start the application
python app.py
