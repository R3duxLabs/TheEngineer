#!/bin/bash
# The Engineer - Setup Script
# This script sets up the environment for The Engineer assistant

echo "  _______ _            _____             _                       "
echo " |__   __| |          |  __ \           (_)                      "
echo "    | |  | |__   ___  | |__) |   ___ ___ _ _ __   ___  ___ _ __  "
echo "    | |  | '_ \ / _ \ |  _  /   / _ / __| | '_ \ / _ \/ _ \ '__| "
echo "    | |  | | | |  __/ | | \ \  |  __\__ \ | | | |  __/  __/ |    "
echo "    |_|  |_| |_|\___| |_|  \_\  \___|___/_|_| |_|\___|\___|_|    "
echo "                                                                  "
echo "                      Setup Script                                "
echo ""

# Check if running in Replit
if [ -d "/home/runner" ]; then
  echo "✅ Running in Replit environment"
else
  echo "⚠️ This script is designed for Replit. Some features may not work correctly."
fi

# Create required directories
echo "📁 Creating directories..."
mkdir -p conversations

# Check for Python
if command -v python3 &>/dev/null; then
  PYTHON="python3"
elif command -v python &>/dev/null; then
  PYTHON="python"
else
  echo "❌ Error: Python not found. Please install Python 3."
  exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
$PYTHON -m pip install requests --quiet

# Check for API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "⚠️ ANTHROPIC_API_KEY environment variable not found!"
  echo "  Please add your API key in the Secrets tab (key: ANTHROPIC_API_KEY)"
  echo "  You can still continue with setup, but the assistant won't work until you add your API key."
else
  echo "✅ Anthropic API key found"
fi

# Create or update .replit file
echo "🔧 Configuring Replit environment..."
cat > .replit << 'EOF'
run = "python main.py"
language = "python3"
entrypoint = "main.py"

[nix]
channel = "stable-23_11"

[deployment]
run = "python main.py --web"
deploymentTarget = "cloudrun"
ignorePorts = false

[[ports]]
localPort = 8080
externalPort = 80
EOF

# Update app title in main.py
echo "✏️ Updating application title..."
if [ -f "main.py" ]; then
  # Replace EchoMind with The Engineer in the title
  sed -i 's/EchoMind Claude Assistant/The Engineer/g' main.py
  sed -i 's/EchoMind Claude/The Engineer/g' main.py
  sed -i 's/EchoMind/The Engineer/g' main.py
fi

echo ""
echo "✅ Setup complete! You can now start The Engineer by running:"
echo "   python main.py"
echo ""
echo "📋 Available modes:"
echo "   - Console mode: python main.py"
echo "   - Web interface: python main.py --web"
echo ""
echo "🔍 For web interface, click the Run button and open the webview in Replit"
