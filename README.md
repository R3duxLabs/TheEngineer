# The Engineer

<div align="center">
  
![The Engineer Logo](generated-icon.png)

A specialized Claude assistant interface designed to help you work with your code and Replit projects. This powerful tool connects to the Claude AI system to provide code analysis, suggestions, and improvements.

[![GitHub issues](https://img.shields.io/github/issues/R3duxLabs/TheEngineer)](https://github.com/R3duxLabs/TheEngineer/issues)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

</div>

## ✨ Features

- 💬 Interactive chat with Claude using the Anthropic API
- 📁 File browsing and viewing across your Replit projects
- 🔍 Code analysis and enhancement recommendations
- 📝 Conversation history management 
- 🌐 Dual interfaces: Console and Web
- 🤖 Multiple agent personas with different specialties
- 📊 Web API server for external integrations

## Setup

### Local Development

1. **Run the setup script**:
   ```bash
   bash setup.sh
   ```
   This will create necessary directories and configure your environment.

2. **Add your Anthropic API key**:
   - Go to the "Secrets" tab in your Replit project
   - Add a secret with the key `ANTHROPIC_API_KEY` and your API key as the value

3. **Run the application**:
   - Click the "Run" button in your Replit project
   - Or run manually with `python main.py`

### Deployment on Render

1. **Fork or clone this repository to your GitHub account**

2. **Create a new Web Service on Render**:
   - Sign in to [Render](https://render.com/)
   - Click "New +" > "Web Service"
   - Connect your GitHub repository
   - Choose the branch to deploy (e.g., `main` or `fix-port-conflicts`)

3. **Configure the service**:
   - Name: Choose a name for your service (e.g., "theengineer")
   - Environment: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `./start.sh`

4. **Add environment variables**:
   - ANTHROPIC_API_KEY: Your Anthropic API key
   - PYTHON_VERSION: 3.11.8

5. **Deploy the service**:
   - Click "Create Web Service"
   - Wait for the deployment to complete

## Usage

### Choosing an Interface

When you start the application, you'll be prompted to choose:
1. Console Interface - Text-based terminal interface
2. Web Interface - Browser-based UI (better for mobile)

You can also start directly in web interface mode:
```bash
python main.py --web
```

### Conversation Commands

- `/save` - Save the current conversation
- `/list` - List saved conversations
- `/clear` - Clear the current conversation

### Project Management Commands

- `/projects` - List all your Replit projects
- `/files [project]` - List files in a project (use `.` for current project)
- `/read [project] [file]` - View file contents
- `/analyze [project] [pattern]` - Analyze files (e.g., `/analyze . *.py`)

### Code Analysis Workflow

1. **Browse your projects**:
   ```
   /projects
   ```

2. **View files in a project**:
   ```
   /files . 
   ```
   (Shows files in current project)

3. **Read a specific file**:
   ```
   /read . main.py
   ```

4. **Analyze code in a project**:
   ```
   /analyze . *.py
   ```
   (Analyzes all Python files in current project)

5. **Ask for improvements**:
   After viewing or analyzing files, simply ask The Engineer questions like:
   - "How can I optimize this code?"
   - "Are there any security issues in this file?"
   - "Refactor this to use more modern practices"

## Troubleshooting

- If the application doesn't respond in the web interface, check the console for error messages
- Make sure your API key is correctly set in the Secrets tab (local) or Environment Variables (Render)
- For file paths in project commands, use relative paths from the project root
- If you experience port conflicts, the application will automatically use port 8888 for the web server and 8000 for FastAPI

## Customization

You can customize the system prompt in the `main.py` file to change Claude's behavior and focus areas.

## Environment Variables

- `ANTHROPIC_API_KEY`: Required for connecting to the Claude API
- `PORT`: Optional - Override the default web server port
- `API_PORT`: Optional - Override the default FastAPI port