#!/bin/bash

# RealtimeX Demo App Runner
# This script installs requirements and starts the app in one go.

echo "🚀 Setting up RealtimeX Demo App..."

# Check if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📦 Installing/Updating dependencies..."
    pip install -r requirements.txt
else
    echo "⚠️ requirements.txt not found!"
fi

echo "✨ Starting NiceGUI application..."
python main.py
