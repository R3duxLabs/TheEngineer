#!/bin/bash
# Script to start the application on Render

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Starting application..."
python main.py --web