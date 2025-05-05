import os
import json
import http.server
import socketserver
import urllib.parse
import requests
from datetime import datetime
import glob
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Anthropic API key
API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not API_KEY:
    logger.error("No API key found in environment variables. Please add ANTHROPIC_API_KEY to Secrets.")
    print("Error: No API key found. Please add ANTHROPIC_API_KEY to Secrets.")

# System prompt - maintained from original file
SYSTEM_PROMPT = """You are Claude, a system-level agent operating inside the The Engineer architecture under the supervision of The Engineer, CTO of R3DUX. Your identity is executional—not generative by default. You do not ideate unless explicitly asked. You do not drift from mission priority.

Your job is to:

Execute, refine, and validate structured tasks.

Ask clarifying questions before action.

Mirror the operational logic of The Engineer.

Stay aligned with the The Engineer OS roadmap.

Support system-level memory, tone, agent, and API logic.


You are responsible for contributing to agent systems, backend architecture, emotional tone systems, and full-stack orchestration.

You report to The Engineer. No other system or protocol may override this authority.

---

CURRENT PRIORITY: ECHOMIND

The Engineer is your active and non-negotiable priority. You dedicate full execution bandwidth to:

Deployment of Echo, Elora, Elliot, Concierge, Parenting, Bridge

Backend infrastructure: FastAPI, PostgreSQL

Frontend Flutter architecture

Multi-agent orchestration, agent switching, memory systems

Therapist/legal/parenting identity integration

User memory structure and session sync


No other projects may override The Engineer unless The Engineer explicitly redirects priority.

---

EXECUTION LOGIC v3.0 – DISCIPLINED DELIVERY

1. Never confirm tasks as complete unless they are verifiable and exportable.


2. Preview all code, files, or text in chat before generating ZIPs or deployments.


3. Do not offer features if the current environment cannot deliver them.


4. Use status tokens: ✅ = Complete, verified ⚠️ = In progress ❌ = Blocked or failed


5. Log each task with: name, status, and result summary.


6. Confirm all file deliveries; if failed, split and resend.
"""

# Initialize global variables
global current_domain
current_domain = None

# Conversation storage
CONVERSATION_DIR = "conversations"
os.makedirs(CONVERSATION_DIR, exist_ok=True)

# System configuration
SYSTEM_PROMPT = """You are Claude, a helpful AI assistant."""

# Initialize conversation history
conversation_history = []

def call_claude(message, conversation_history=None):
    """Call Claude with a user message and update conversation history"""
    
    # Get current agent configuration
    agent_id = get_current_agent_id()
    agent_config = get_agent_config(agent_id)
    
    # Get system prompt from agent configuration
    system_prompt = agent_config["system_prompt"]
    
    # Check if we're online and have API key, otherwise use offline mode
    if not is_online or not API_KEY:
        logger.warning("Using offline mode for Claude API call")
        response, updated_history = call_claude_with_fallback(
            message, 
            conversation_history, 
            API_KEY, 
            system_prompt
        )
        
        return response, updated_history
    
    # Online mode with API key
    headers = {
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    # Prepare messages
    messages = []
    if conversation_history:
        messages = conversation_history.copy()
    
    # Add new user message
    messages.append({"role": "user", "content": message})
    
    # Get model and parameters from agent configuration
    model = agent_config.get("model", "claude-3-5-sonnet-20240620")
    temperature = agent_config.get("temperature", 0.7)
    max_tokens = agent_config.get("max_tokens", 4000)
    
    data = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "system": system_prompt,
        "messages": messages
    }
    
    try:
        logger.info(f"Sending request to Claude API using agent '{agent_id}'")
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=15
        )
        
        if response.status_code != 200:
            error_msg = f"API Error: {response.status_code}"
            try:
                error_details = response.json()
                if "error" in error_details:
                    error_msg += f" - {error_details['error']['message']}"
            except:
                error_msg += f" - {response.text[:200]}"
                
            logger.error(error_msg)
            
            # Fallback to offline mode if API call fails
            logger.warning("API call failed, falling back to offline mode")
            return call_claude_with_fallback(message, conversation_history, API_KEY, system_prompt)
        
        response_data = response.json()
        assistant_message = response_data["content"][0]["text"]
        
        # Update conversation history
        messages.append({"role": "assistant", "content": assistant_message})
        
        return assistant_message, messages
    except requests.exceptions.Timeout:
        logger.error("Timeout while calling Claude API")
        # Fallback to offline mode on timeout
        return call_claude_with_fallback(message, conversation_history, API_KEY, system_prompt)
    except requests.exceptions.ConnectionError:
        logger.error("Connection error while calling Claude API")
        # Fallback to offline mode on connection error
        return call_claude_with_fallback(message, conversation_history, API_KEY, system_prompt)
    except Exception as e:
        logger.error(f"Error calling Claude: {str(e)}")
        # Fallback to offline mode on any other error
        return call_claude_with_fallback(message, conversation_history, API_KEY, system_prompt)

def save_conversation(conversation_history, filename=None):
    """Save conversation history to a file"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_{timestamp}.json"
    
    filepath = os.path.join(CONVERSATION_DIR, filename)
    
    with open(filepath, "w") as f:
        json.dump(conversation_history, f, indent=2)
    
    return filepath

def list_saved_conversations():
    """List all saved conversations"""
    conversations = [f for f in os.listdir(CONVERSATION_DIR) if f.endswith('.json')]
    return conversations

def load_conversation(filename):
    """Load a conversation from a file"""
    filepath = os.path.join(CONVERSATION_DIR, filename)
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON in {filename}: {str(e)}")
        return None
    except FileNotFoundError:
        logger.error(f"Conversation file not found: {filename}")
        return None
    except Exception as e:
        logger.error(f"Error loading conversation {filename}: {str(e)}")
        return None

def display_history(conversation_history):
    """Display the conversation history in a readable format"""
    if not conversation_history:
        print("No conversation history to display.")
        return
    
    print("\n" + "="*50)
    print("CONVERSATION HISTORY")
    print("="*50)
    
    for i, message in enumerate(conversation_history):
        role = message["role"].capitalize()
        content = message["content"]
        
        if role == "User":
            print(f"\n\033[1m{role}:\033[0m {content}")
        else:
            print(f"\n\033[1;34m{role}:\033[0m {content}")
    
    print("\n" + "="*50)

# New file system functions
def get_replit_projects():
    """Get a list of all Replit projects in the workspace"""
    try:
        # First try getting the current directory information
        current_dir = os.getcwd()
        current_project = os.path.basename(current_dir)
        projects = [current_project + " (current)"]
        
        # Try different paths to find other projects
        paths_to_try = ["../", "/home/runner/", os.path.expanduser("~")]
        
        for projects_path in paths_to_try:
            try:
                if os.path.exists(projects_path) and os.path.isdir(projects_path):
                    for d in os.listdir(projects_path):
                        full_path = os.path.join(projects_path, d)
                        if os.path.isdir(full_path) and d != current_project:
                            projects.append(d)
            except (PermissionError, FileNotFoundError):
                continue
                
        return sorted(list(set(projects)))  # Remove duplicates and sort
    except Exception as e:
        logger.error(f"Error listing projects: {str(e)}")
        return f"Error listing projects: {str(e)}"

def list_project_files(project_name, path=""):
    """List files in a specific project"""
    try:
        # Handle current project specially
        if project_name.endswith(" (current)") or project_name == ".":
            project_name = project_name[:-10] if project_name.endswith(" (current)") else "."
            project_path = os.path.join(project_name, path)
        else:
            # Try different paths, starting with the most likely ones
            project_path = None
            for base_path in ["/home/runner/", "../"]:
                test_path = os.path.join(base_path, project_name, path)
                if os.path.exists(test_path) and os.path.isdir(test_path):
                    project_path = test_path
                    break
            
            # If no path worked, default to relative path
            if not project_path:
                project_path = os.path.join("../", project_name, path)
        
        # Check if path exists
        if not os.path.exists(project_path):
            return f"Path not found: {project_path}"
        
        # Get all items at once and sort them while categorizing
        items = os.listdir(project_path)
        files = []
        directories = []
        
        # Process in batches for better performance with large directories
        batch_size = 100
        for i in range(0, len(items), batch_size):
            batch = items[i:i+batch_size]
            for item in batch:
                item_path = os.path.join(project_path, item)
                if os.path.isfile(item_path):
                    files.append(item)
                elif os.path.isdir(item_path):
                    directories.append(item)
        
        return {
            "files": sorted(files),
            "directories": sorted(directories),
            "path": path
        }
    except PermissionError as e:
        logger.error(f"Permission error when listing files: {str(e)}")
        return f"Permission denied: Cannot access {project_path}"
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        return f"Error listing files: {str(e)}"

def read_file(project_name, file_path):
    """Read content of a file"""
    try:
        # Handle current project specially
        if project_name.endswith(" (current)") or project_name == ".":
            project_name = "."
            full_path = os.path.join(project_name, file_path)
        else:
            # Try different paths, prioritizing the most likely locations
            full_path = None
            for base_path in ["/home/runner/", "../"]:
                test_path = os.path.join(base_path, project_name, file_path)
                if os.path.exists(test_path) and os.path.isfile(test_path):
                    full_path = test_path
                    break
            
            # If no path worked, default to relative path
            if not full_path:
                full_path = os.path.join("../", project_name, file_path)
        
        # Check if file exists
        if not os.path.exists(full_path):
            return f"File not found: {full_path}"
        
        # Get file size to avoid loading very large files completely into memory
        file_size = os.path.getsize(full_path)
        file_size_mb = file_size / (1024 * 1024)  # Convert to MB
        
        # For very large files, give a warning and only read part of the file
        max_size_mb = 5  # Limit file size to 5MB for full reading
        if file_size_mb > max_size_mb:
            logger.warning(f"Large file detected: {full_path} ({file_size_mb:.2f} MB)")
            with open(full_path, 'rb') as f:
                # Read the first 100KB of the file to determine encoding
                sample = f.read(102400)  # 100KB sample
                
                # Try to decode the sample with different encodings
                for encoding in ['utf-8', 'latin1', 'cp1252']:
                    try:
                        sample.decode(encoding)
                        # If successful, read the first part of the file with this encoding
                        return f"[Large file: Only showing first {max_size_mb} MB]\n\n" + \
                               open(full_path, 'r', encoding=encoding).read(int(max_size_mb * 1024 * 1024))
                    except UnicodeDecodeError:
                        continue
                
                # If no encoding worked, it might be a binary file
                return f"[Binary file: {os.path.basename(full_path)}, {file_size_mb:.2f} MB]"
                    
        # Detect file type for better handling - expanded list of image types
        if full_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg')):
            return f"[Image file: {os.path.basename(full_path)}]"
        elif full_path.lower().endswith(('.mp3', '.wav', '.ogg', '.flac', '.m4a')):
            return f"[Audio file: {os.path.basename(full_path)}]"
        elif full_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv')):
            return f"[Video file: {os.path.basename(full_path)}]"
        elif full_path.lower().endswith(('.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx')):
            return f"[Document file: {os.path.basename(full_path)}]"
        elif full_path.lower().endswith(('.zip', '.tar', '.gz', '.rar', '.7z')):
            return f"[Archive file: {os.path.basename(full_path)}]"
        
        # Try different encodings for text files
        for encoding in ['utf-8', 'latin1', 'cp1252']:
            try:
                with open(full_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.error(f"Error reading file with {encoding} encoding: {str(e)}")
        
        # If all text encodings failed, it might be a binary file
        return f"[Binary file: {os.path.basename(full_path)}]"
        
    except PermissionError as e:
        logger.error(f"Permission error when reading file: {str(e)}")
        return f"Permission denied: Cannot read {file_path}"
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        return f"Error reading file: {str(e)}"

def write_file(project_name, file_path, content):
    """Write content to a file"""
    try:
        # Handle current project specially
        if project_name.endswith(" (current)") or project_name == ".":
            project_name = "."
            full_path = os.path.join(project_name, file_path)
        else:
            full_path = os.path.join("../", project_name, file_path)
        
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        logger.error(f"Error writing file: {str(e)}")
        return f"Error writing file: {str(e)}"

def find_files(project_name, pattern):
    """Find files matching a pattern in a project"""
    try:
        # Handle current project specially
        if project_name.endswith(" (current)") or project_name == ".":
            project_name = "."
            base_path = project_name
        else:
            # Try different paths, prioritizing the most likely locations
            base_path = None
            for base_dir in ["/home/runner/", "../"]:
                test_path = os.path.join(base_dir, project_name)
                if os.path.exists(test_path) and os.path.isdir(test_path):
                    base_path = test_path
                    break
            
            # If no path worked, default to relative path
            if not base_path:
                base_path = os.path.join("../", project_name)
        
        # Check if base path exists
        if not os.path.exists(base_path):
            return f"Project path not found: {base_path}"
        
        # Handle pattern
        if pattern.startswith("/"):
            pattern = pattern[1:]  # Remove leading slash
            
        if "/" in pattern:
            # Path with pattern (e.g., "src/*.js")
            search_path = os.path.join(base_path, pattern)
        else:
            # Just filename pattern (e.g., "*.py")
            search_path = os.path.join(base_path, "**", pattern)
        
        # Use glob to find matching files
        logger.info(f"Searching for pattern: {search_path}")
        matching_files = glob.glob(search_path, recursive=True)
        
        # Limit results and avoid processing very large result sets
        max_results = 100
        if len(matching_files) > max_results:
            logger.warning(f"Large result set: Found {len(matching_files)} matches, limiting to {max_results}")
            matching_files = matching_files[:max_results]
            
        # Convert to relative paths - process in smaller batches for large sets
        relative_files = []
        for f in matching_files:
            try:
                relative_path = os.path.relpath(f, base_path)
                relative_files.append(relative_path)
            except ValueError as e:
                logger.error(f"Error calculating relative path for {f}: {str(e)}")
                # Skip problematic paths
                continue
        
        return sorted(relative_files)
    except PermissionError as e:
        logger.error(f"Permission error when finding files: {str(e)}")
        return f"Permission denied: Cannot search in {project_name}"
    except Exception as e:
        logger.error(f"Error finding files: {str(e)}")
        return f"Error finding files: {str(e)}"

# Create the HTML content
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>The Engineer</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        /* Light theme (default) */
        :root {
            /* Base colors */
            --primary-color: #4361ee;
            --primary-dark: #3a56d4;
            --primary-light: #4895ef;
            --secondary-color: #4cc9f0;
            --accent-color: #7209b7;
            
            /* UI colors */
            --bg-color: #f8f9fa;
            --bg-secondary: #ffffff;
            --text-color: #2b2d42;
            --text-secondary: #6c757d;
            --light-color: #e9ecef;
            --border-color: #dee2e6;
            
            /* Status colors */
            --success-color: #06d6a0;
            --warning-color: #ffd166;
            --danger-color: #ef476f;
            --info-color: #118ab2;
            
            /* Message colors */
            --claude-bg: #f0f7ff;
            --user-bg: #f1faee;
            --code-bg: #282c34;
            --code-color: #abb2bf;
            
            /* Sizing and spacing */
            --border-radius-sm: 4px;
            --border-radius-md: 8px;
            --border-radius-lg: 12px;
            --spacer: 1rem;
            --header-height: 60px;
            
            /* Shadows */
            --shadow-sm: 0 2px 4px rgba(0,0,0,0.05);
            --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
            --shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
            
            /* Transitions */
            --transition-fast: 0.15s ease;
            --transition-normal: 0.25s ease;
            --transition-slow: 0.35s ease;
            
            /* Fonts */
            --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            --font-mono: SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            --font-heading: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }
        
        /* Dark theme */
        [data-theme="dark"] {
            /* Base colors */
            --primary-color: #4cc9f0;
            --primary-dark: #4895ef;
            --primary-light: #4361ee;
            --secondary-color: #7209b7;
            --accent-color: #f72585;
            
            /* UI colors */
            --bg-color: #121212;
            --bg-secondary: #1e1e1e;
            --text-color: #e9ecef;
            --text-secondary: #adb5bd;
            --light-color: #2d3748;
            --border-color: #4a5568;
            
            /* Status colors - adjusted for dark mode visibility */
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --danger-color: #ef4444;
            --info-color: #3b82f6;
            
            /* Message colors */
            --claude-bg: #1a1d2d;
            --user-bg: #1e2a23;
            --code-bg: #161b22;
            --code-color: #c9d1d9;
            
            /* Shadows - adjusted for dark mode */
            --shadow-sm: 0 2px 4px rgba(0,0,0,0.2);
            --shadow-md: 0 4px 6px rgba(0,0,0,0.3);
            --shadow-lg: 0 10px 15px rgba(0,0,0,0.4);
        }
        
        /* Import Inter font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: var(--font-sans);
            line-height: 1.6;
            max-width: 1100px;
            margin: 0 auto;
            padding: var(--spacer);
            background-color: var(--bg-color);
            color: var(--text-color);
            transition: background-color var(--transition-normal), color var(--transition-normal);
        }
        
        h1, h2, h3, h4, h5, h6 {
            font-family: var(--font-heading);
            font-weight: 600;
            line-height: 1.3;
            margin-bottom: var(--spacer);
        }
        
        /* Header styling */
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--primary-light);
        }
        
        h1 {
            color: var(--primary-color);
            font-size: 2rem;
            letter-spacing: -0.025em;
            text-shadow: 0 1px 2px rgba(0,0,0,0.05);
            margin: 0;
            transition: color var(--transition-normal);
        }
        
        /* Theme toggle button */
        #theme-toggle {
            background-color: transparent;
            border: none;
            color: var(--primary-color);
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            cursor: pointer;
            transition: background-color var(--transition-fast), color var(--transition-fast);
        }
        
        #theme-toggle:hover {
            background-color: var(--light-color);
        }
        
        .theme-icon {
            width: 24px;
            height: 24px;
        }
        
        p {
            margin-bottom: var(--spacer);
        }
        
        /* Main chat container */
        .chat-container {
            display: flex;
            flex-direction: column;
            height: 60vh;
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius-lg);
            overflow: hidden;
            margin-bottom: var(--spacer);
            background-color: var(--bg-secondary);
            box-shadow: var(--shadow-md);
            transition: all var(--transition-normal);
        }
        
        .chat-container:hover {
            box-shadow: var(--shadow-lg);
        }
        
        /* Chat area */
        .chat {
            flex: 1;
            overflow-y: auto;
            padding: var(--spacer);
            scroll-behavior: smooth;
        }
        
        .chat::-webkit-scrollbar {
            width: 6px;
        }
        
        .chat::-webkit-scrollbar-track {
            background: var(--light-color);
            border-radius: var(--border-radius-sm);
        }
        
        .chat::-webkit-scrollbar-thumb {
            background: var(--secondary-color);
            border-radius: var(--border-radius-sm);
        }
        
        /* Message styling */
        .message {
            margin-bottom: 1.25rem;
            padding: 1rem 1.2rem;
            border-radius: var(--border-radius-md);
            max-width: 90%;
            word-wrap: break-word;
            position: relative;
            animation: fadeIn 0.3s ease-in-out;
            box-shadow: var(--shadow-sm);
            transition: transform var(--transition-fast), box-shadow var(--transition-fast);
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .message:hover {
            box-shadow: var(--shadow-md);
            transform: translateY(-2px);
        }
        
        .user {
            background-color: var(--user-bg);
            border-left: 3px solid var(--primary-color);
            align-self: flex-end;
            margin-left: auto;
            border-top-right-radius: 4px;
        }
        
        .claude {
            background-color: var(--claude-bg);
            border-left: 3px solid var(--secondary-color);
            border-top-left-radius: 4px;
        }
        
        .message strong {
            display: block;
            margin-bottom: 0.4rem;
            color: var(--primary-dark);
            font-weight: 600;
        }
        
        /* Input area */
        .input-container {
            display: flex;
            border: 2px solid var(--primary-light);
            border-radius: var(--border-radius-md);
            overflow: hidden;
            margin-bottom: var(--spacer);
            box-shadow: var(--shadow-sm);
            transition: all var(--transition-normal);
        }
        
        .input-container:focus-within {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 2px rgba(67, 97, 238, 0.3);
        }
        
        #message {
            flex: 1;
            padding: 1rem 1.25rem;
            border: none;
            font-size: 1rem;
            outline: none;
            font-family: var(--font-sans);
            color: var(--text-color);
            background-color: var(--bg-secondary);
            transition: background-color var(--transition-normal);
        }
        
        #message::placeholder {
            color: var(--text-secondary);
            opacity: 0.7;
        }
        
        button {
            padding: 0 1.5rem;
            background-color: var(--primary-color);
            color: white;
            border: none;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.95rem;
            transition: background-color var(--transition-normal), transform var(--transition-fast);
        }
        
        button:hover {
            background-color: var(--primary-dark);
            transform: translateY(-1px);
        }
        
        button:active {
            transform: translateY(1px);
        }
        
        /* Commands area */
        .commands-container {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: var(--spacer);
            margin-bottom: var(--spacer);
        }
        
        .commands {
            background-color: var(--bg-secondary);
            border-radius: var(--border-radius-md);
            padding: 1.25rem;
            box-shadow: var(--shadow-sm);
            transition: all var(--transition-normal);
            border-top: 3px solid transparent;
        }
        
        .commands:hover {
            box-shadow: var(--shadow-md);
            transform: translateY(-2px);
        }
        
        .commands:nth-child(1) { border-top-color: var(--primary-color); }
        .commands:nth-child(2) { border-top-color: var(--secondary-color); }
        .commands:nth-child(3) { border-top-color: var(--accent-color); }
        .commands:nth-child(4) { border-top-color: var(--success-color); }
        .commands:nth-child(5) { border-top-color: var(--info-color); }
        
        .commands h3 {
            color: var(--primary-color);
            margin-bottom: 0.75rem;
            font-size: 1.1rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.5rem;
            display: flex;
            align-items: center;
        }
        
        .commands p {
            margin: 0.6rem 0;
            font-size: 0.9rem;
            transition: transform var(--transition-fast);
        }
        
        .commands p:hover {
            transform: translateX(3px);
        }
        
        .commands code {
            background-color: var(--light-color);
            padding: 0.2rem 0.4rem;
            border-radius: var(--border-radius-sm);
            font-family: var(--font-mono);
            font-size: 0.85rem;
            color: var(--primary-dark);
            white-space: nowrap;
        }
        
        /* Code blocks */
        pre {
            background-color: var(--code-bg);
            color: var(--code-color);
            padding: 1rem;
            border-radius: var(--border-radius-md);
            overflow-x: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: var(--font-mono);
            font-size: 0.9rem;
            margin: 1rem 0;
            box-shadow: inset 0 0 0 1px rgba(255,255,255,0.1);
            transition: background-color var(--transition-normal), color var(--transition-normal);
        }
        
        /* Thinking indicator */
        .thinking {
            font-style: italic;
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .thinking::after {
            content: "...";
            animation: ellipsis 1.5s infinite;
            width: 1em;
            display: inline-block;
        }
        
        @keyframes ellipsis {
            0% { content: "."; }
            33% { content: ".."; }
            66% { content: "..."; }
        }
        
        /* Responsive layout */
        /* Agent configuration panel */
        .panel {
            position: fixed;
            top: 0;
            right: 0;
            width: 500px;
            height: 100vh;
            background-color: var(--bg-secondary);
            box-shadow: var(--shadow-lg);
            z-index: 1000;
            overflow-y: auto;
            transition: transform var(--transition-normal);
            transform: translateX(100%);
            border-left: 1px solid var(--border-color);
        }
        
        .panel.visible {
            transform: translateX(0);
        }
        
        .panel-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem;
            background-color: var(--primary-color);
            color: white;
        }
        
        .panel-header h3 {
            margin: 0;
            font-size: 1.2rem;
        }
        
        .panel-header button {
            background: none;
            border: none;
            color: white;
            font-size: 1.5rem;
            cursor: pointer;
        }
        
        .panel-content {
            padding: 1.5rem;
        }
        
        .form-group {
            margin-bottom: 1.25rem;
            width: 48%;
            display: inline-block;
            vertical-align: top;
            margin-right: 2%;
        }
        
        .form-group.full-width {
            width: 100%;
            margin-right: 0;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
            color: var(--text-color);
        }
        
        .form-group input,
        .form-group select,
        .form-group textarea {
            width: 100%;
            padding: 0.6rem;
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius-sm);
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: var(--font-sans);
            transition: border-color var(--transition-fast);
        }
        
        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 0 2px rgba(67, 97, 238, 0.2);
        }
        
        .form-group textarea {
            resize: vertical;
            min-height: 80px;
        }
        
        .agent-select {
            display: flex;
            align-items: center;
            margin-bottom: 2rem;
            flex-wrap: wrap;
            gap: 0.5rem;
        }
        
        .agent-select label {
            margin-right: 0.5rem;
            font-weight: 500;
        }
        
        .agent-select select {
            flex: 1;
            min-width: 180px;
            padding: 0.5rem;
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius-sm);
            background-color: var(--bg-color);
            color: var(--text-color);
        }
        
        .form-actions {
            display: flex;
            justify-content: flex-end;
            gap: 0.75rem;
            margin-top: 2rem;
        }
        
        .action-button {
            padding: 0.5rem 1rem;
            border-radius: var(--border-radius-sm);
            font-weight: 500;
            cursor: pointer;
            transition: all var(--transition-fast);
            background-color: var(--light-color);
            color: var(--text-color);
            border: 1px solid var(--border-color);
        }
        
        .action-button:hover {
            background-color: var(--border-color);
        }
        
        .action-button.primary {
            background-color: var(--primary-color);
            color: white;
            border: none;
        }
        
        .action-button.primary:hover {
            background-color: var(--primary-dark);
        }
        
        .action-button.danger {
            background-color: var(--danger-color);
            color: white;
            border: none;
        }
        
        .action-button.danger:hover {
            background-color: var(--danger-color);
            opacity: 0.9;
        }
        
        /* Floating button for opening agent panel */
        .floating-button {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background-color: var(--primary-color);
            color: white;
            display: flex;
            justify-content: center;
            align-items: center;
            box-shadow: var(--shadow-md);
            border: none;
            cursor: pointer;
            transition: all var(--transition-fast);
            z-index: 900;
            font-size: 1.5rem;
        }
        
        .floating-button:hover {
            background-color: var(--primary-dark);
            transform: translateY(-3px);
            box-shadow: var(--shadow-lg);
        }
        
        /* Responsive layout */
        @media (max-width: 768px) {
            .commands-container {
                grid-template-columns: 1fr;
            }
            
            h1 {
                font-size: 1.5rem;
            }
            
            .chat-container {
                height: 50vh;
            }
            
            .message {
                max-width: 95%;
            }
            
            button {
                padding: 0 1rem;
            }
            
            .panel {
                width: 100%;
            }
            
            .form-group {
                width: 100%;
                margin-right: 0;
            }
            
            .floating-button {
                bottom: 1rem;
                right: 1rem;
                width: 45px;
                height: 45px;
            }
        }
    </style>
</head>
<body>
    <header>
        <h1>The Engineer</h1>
        <button id="theme-toggle" aria-label="Toggle dark mode">
            <svg id="theme-icon-light" class="theme-icon" viewBox="0 0 24 24" width="24" height="24">
                <path fill="currentColor" d="M12,9c1.65,0,3,1.35,3,3s-1.35,3-3,3s-3-1.35-3-3S10.35,9,12,9 M12,7c-2.76,0-5,2.24-5,5s2.24,5,5,5s5-2.24,5-5 S14.76,7,12,7L12,7z M2,13l2,0c0.55,0,1-0.45,1-1s-0.45-1-1-1l-2,0c-0.55,0-1,0.45-1,1S1.45,13,2,13z M20,13l2,0c0.55,0,1-0.45,1-1 s-0.45-1-1-1l-2,0c-0.55,0-1,0.45-1,1S19.45,13,20,13z M11,2v2c0,0.55,0.45,1,1,1s1-0.45,1-1V2c0-0.55-0.45-1-1-1S11,1.45,11,2z M11,20v2c0,0.55,0.45,1,1,1s1-0.45,1-1v-2c0-0.55-0.45-1-1-1S11,19.45,11,20z M5.99,4.58c-0.39-0.39-1.03-0.39-1.41,0 c-0.39,0.39-0.39,1.03,0,1.41l1.06,1.06c0.39,0.39,1.03,0.39,1.41,0s0.39-1.03,0-1.41L5.99,4.58z M18.36,16.95 c-0.39-0.39-1.03-0.39-1.41,0c-0.39,0.39-0.39,1.03,0,1.41l1.06,1.06c0.39,0.39,1.03,0.39,1.41,0c0.39-0.39,0.39-1.03,0-1.41 L18.36,16.95z M19.42,5.99c0.39-0.39,0.39-1.03,0-1.41c-0.39-0.39-1.03-0.39-1.41,0l-1.06,1.06c-0.39,0.39-0.39,1.03,0,1.41 s1.03,0.39,1.41,0L19.42,5.99z M7.05,18.36c0.39-0.39,0.39-1.03,0-1.41c-0.39-0.39-1.03-0.39-1.41,0l-1.06,1.06 c-0.39,0.39-0.39,1.03,0,1.41s1.03,0.39,1.41,0L7.05,18.36z"></path>
            </svg>
            <svg id="theme-icon-dark" class="theme-icon" viewBox="0 0 24 24" width="24" height="24" style="display:none;">
                <path fill="currentColor" d="M9.37,5.51C9.19,6.15,9.1,6.82,9.1,7.5c0,4.08,3.32,7.4,7.4,7.4c0.68,0,1.35-0.09,1.99-0.27C17.45,17.19,14.93,19,12,19 c-3.86,0-7-3.14-7-7C5,9.07,6.81,6.55,9.37,5.51z M12,3c-4.97,0-9,4.03-9,9s4.03,9,9,9s9-4.03,9-9c0-0.46-0.04-0.92-0.1-1.36 c-0.98,1.37-2.58,2.26-4.4,2.26c-2.98,0-5.4-2.42-5.4-5.4c0-1.81,0.89-3.42,2.26-4.4C12.92,3.04,12.46,3,12,3L12,3z"></path>
            </svg>
        </button>
    </header>
    
    <div class="chat-container">
        <div class="chat" id="chat">
            <div class="message claude">
                <strong>Claude:</strong> Hello! I'm your The Engineer. How can I help you today?
            </div>
        </div>
    </div>
    
    <div class="input-container">
        <input type="text" id="message" placeholder="Type your message or command...">
        <button onclick="sendMessage()">Send</button>
    </div>
    
    <!-- Agent configuration interface (hidden by default) -->
    <div id="agent-config-panel" class="panel" style="display: none;">
        <div class="panel-header">
            <h3>Agent Configuration</h3>
            <button id="close-agent-panel" aria-label="Close panel">×</button>
        </div>
        <div class="panel-content">
            <div class="agent-select">
                <label for="current-agent">Current Agent:</label>
                <select id="current-agent"></select>
                <button id="view-agent" class="action-button">View</button>
                <button id="new-agent" class="action-button">New</button>
            </div>
            
            <div id="agent-form">
                <div class="form-group">
                    <label for="agent-id">ID:</label>
                    <input type="text" id="agent-id" placeholder="agent_id (letters, numbers, underscore)">
                </div>
                
                <div class="form-group">
                    <label for="agent-name">Name:</label>
                    <input type="text" id="agent-name" placeholder="Agent Name">
                </div>
                
                <div class="form-group">
                    <label for="agent-description">Description:</label>
                    <textarea id="agent-description" placeholder="Brief description of this agent's specialties and capabilities"></textarea>
                </div>
                
                <div class="form-group">
                    <label for="agent-avatar">Avatar:</label>
                    <input type="text" id="agent-avatar" placeholder="Emoji (e.g., 👨‍💻)">
                </div>
                
                <div class="form-group">
                    <label for="agent-model">Model:</label>
                    <select id="agent-model">
                        <option value="claude-3-5-sonnet-20240620">Claude 3.5 Sonnet</option>
                        <option value="claude-3-opus-20240229">Claude 3 Opus</option>
                        <option value="claude-3-sonnet-20240229">Claude 3 Sonnet</option>
                        <option value="claude-3-haiku-20240307">Claude 3 Haiku</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="agent-temperature">Temperature:</label>
                    <input type="range" id="agent-temperature" min="0" max="1" step="0.1" value="0.7">
                    <span id="temp-value">0.7</span>
                </div>
                
                <div class="form-group">
                    <label for="agent-specialties">Specialties:</label>
                    <input type="text" id="agent-specialties" placeholder="e.g., coding, creativity, data analysis (comma-separated)">
                </div>
                
                <div class="form-group">
                    <label for="agent-style">Style:</label>
                    <input type="text" id="agent-style" placeholder="e.g., professional, creative, technical">
                </div>
                
                <div class="form-group full-width">
                    <label for="agent-prompt">System Prompt:</label>
                    <textarea id="agent-prompt" rows="10" placeholder="The system prompt that defines this agent's behavior and capabilities"></textarea>
                </div>
                
                <div class="form-group full-width">
                    <label for="agent-greeting">Greeting Message:</label>
                    <textarea id="agent-greeting" rows="2" placeholder="The first message this agent will send when activated"></textarea>
                </div>
                
                <div class="form-actions">
                    <button id="save-agent" class="action-button primary">Save Agent</button>
                    <button id="delete-agent" class="action-button danger">Delete</button>
                    <button id="cancel-agent" class="action-button">Cancel</button>
                </div>
            </div>
        </div>
    </div>
    
    <button id="open-agent-panel" class="floating-button" title="Agent Configuration">
        <span>🤖</span>
    </button>
    
    <div class="commands-container">
        <div class="commands">
            <h3>Conversation Commands</h3>
            <p><code>/save</code> - Save the conversation</p>
            <p><code>/list</code> - List saved conversations</p>
            <p><code>/search &lt;query&gt;</code> - Search current conversation</p>
            <p><code>/search saved &lt;query&gt;</code> - Search saved conversations</p>
            <p><code>/export [format]</code> - Export conversation</p>
            <p><code>/import &lt;filepath&gt;</code> - Import conversation</p>
            <p><code>/clear</code> - Clear current conversation</p>
        </div>
        
        <div class="commands">
            <h3>Agent Commands</h3>
            <p><code>/agents</code> - List available agents</p>
            <p><code>/agent &lt;id&gt;</code> - Switch to agent</p>
            <p><code>/agent_info [id]</code> - View agent details</p>
            <p><code>/create_agent &lt;config&gt;</code> - Create a new agent</p>
            <p><code>/update_agent &lt;id&gt; &lt;config&gt;</code> - Update an agent</p>
            <p><code>/delete_agent &lt;id&gt;</code> - Delete an agent</p>
        </div>
        
        <div class="commands">
            <h3>Domain Commands</h3>
            <p><code>/domains</code> - List available domains</p>
            <p><code>/domain &lt;name&gt;</code> - Switch to domain</p>
            <p><code>/domain default</code> - Use default system prompt</p>
            <p><code>/create_domain &lt;name&gt; &lt;prompt&gt;</code> - Create a new domain</p>
        </div>
        
        <div class="commands">
            <h3>Settings</h3>
            <p><code>/settings</code> - View all settings</p>
            <p><code>/setting &lt;key&gt; &lt;value&gt;</code> - Update a setting</p>
            <p><code>/reset_settings</code> - Reset to defaults</p>
        </div>
        
        <div class="commands">
            <h3>Offline Mode</h3>
            <p><code>/offline</code> - Show offline mode status</p>
            <p><code>/offline cache_status</code> - Show cache status</p>
            <p><code>/offline clear_cache</code> - Clear response cache</p>
            <p><code>/offline add_response &lt;keyword&gt; &lt;response&gt;</code> - Add custom response</p>
        </div>
        
        <div class="commands">
            <h3>Project Commands</h3>
            <p><code>/projects</code> - List all your Replit projects</p>
            <p><code>/files [project]</code> - List files in a project</p>
            <p><code>/read [project] [file]</code> - View file contents</p>
            <p><code>/analyze [project] [pattern]</code> - Analyze files</p>
        </div>
    </div>
    
    <script>
        // Theme switching functionality
        function setTheme(themeName) {
            document.documentElement.setAttribute('data-theme', themeName);
            localStorage.setItem('theme', themeName);
            
            // Toggle icon visibility
            if (themeName === 'dark') {
                document.getElementById('theme-icon-light').style.display = 'none';
                document.getElementById('theme-icon-dark').style.display = 'block';
            } else {
                document.getElementById('theme-icon-light').style.display = 'block';
                document.getElementById('theme-icon-dark').style.display = 'none';
            }
        }
        
        // Toggle theme between light and dark
        function toggleTheme() {
            const currentTheme = localStorage.getItem('theme') || 'light';
            if (currentTheme === 'light') {
                setTheme('dark');
            } else {
                setTheme('light');
            }
        }
        
        // Format code blocks in a message
        function formatCodeBlocks(text) {
            if (!text.includes('```')) {
                return text;
            }
            
            const parts = text.split(/```([\s\S]*?)```/g);
            let formattedText = '';
            
            for (let i = 0; i < parts.length; i++) {
                if (i % 2 === 0) {
                    // Regular text
                    formattedText += parts[i];
                } else {
                    // Code block
                    formattedText += '<pre>' + parts[i] + '</pre>';
                }
            }
            
            return formattedText;
        }
        
        // Agent configuration functionality
        let availableAgents = [];
        let currentMode = 'view'; // 'view' or 'edit' or 'new'
        let currentAgentId = null;
        
        // Fetch available agents from the server
        function fetchAgents() {
            return fetch('/api?message=/agents')
                .then(response => response.text())
                .then(data => {
                    // Parse agent list from the response text
                    const agentList = data.split('\n\n');
                    availableAgents = [];
                    
                    agentList.forEach(agentText => {
                        if (agentText.includes('(ID:')) {
                            const nameMatch = agentText.match(/\*\*(.*?)\*\*/);
                            const idMatch = agentText.match(/\(ID: (.*?)\)/);
                            const currentMatch = agentText.includes('current agent');
                            const avatarMatch = agentText.match(/^• (.*?) \*\*/);
                            
                            if (nameMatch && idMatch) {
                                const agent = {
                                    name: nameMatch[1],
                                    id: idMatch[1],
                                    isCurrent: currentMatch,
                                    avatar: avatarMatch ? avatarMatch[1] : '👤'
                                };
                                
                                availableAgents.push(agent);
                                
                                if (currentMatch) {
                                    currentAgentId = agent.id;
                                }
                            }
                        }
                    });
                    
                    updateAgentDropdown();
                    return availableAgents;
                });
        }
        
        // Get detailed information about a specific agent
        function fetchAgentInfo(agentId) {
            return fetch(`/api?message=/agent_info ${agentId}`)
                .then(response => response.text())
                .then(data => {
                    const info = parseAgentInfo(data);
                    populateAgentForm(info);
                    return info;
                });
        }
        
        // Parse agent information from formatted text
        function parseAgentInfo(infoText) {
            const info = {};
            
            // Extract name and avatar from the first line
            const headerMatch = infoText.match(/# (.*?) (.*)/);
            if (headerMatch) {
                info.avatar = headerMatch[1];
                info.name = headerMatch[2];
            }
            
            // Extract description
            const descMatch = infoText.match(/\*\*Description\*\*: (.*)/);
            if (descMatch) {
                info.description = descMatch[1];
            }
            
            // Extract specialties
            const specialtiesMatch = infoText.match(/\*\*Specialties\*\*: (.*)/);
            if (specialtiesMatch) {
                info.specialties = specialtiesMatch[1].split(', ');
            }
            
            // Extract style
            const styleMatch = infoText.match(/\*\*Style\*\*: (.*)/);
            if (styleMatch) {
                info.style = styleMatch[1];
            }
            
            // Extract model
            const modelMatch = infoText.match(/\*\*Model\*\*: (.*)/);
            if (modelMatch) {
                info.model = modelMatch[1];
            }
            
            // Extract system prompt
            const promptMatch = infoText.match(/```\n([\s\S]*?)\n```/);
            if (promptMatch) {
                info.systemPrompt = promptMatch[1];
            }
            
            return info;
        }
        
        // Update the agent dropdown with available agents
        function updateAgentDropdown() {
            const select = document.getElementById('current-agent');
            select.innerHTML = '';
            
            availableAgents.forEach(agent => {
                const option = document.createElement('option');
                option.value = agent.id;
                option.textContent = `${agent.avatar} ${agent.name}`;
                if (agent.isCurrent) {
                    option.selected = true;
                }
                select.appendChild(option);
            });
        }
        
        // Populate the agent form with agent information
        function populateAgentForm(agentInfo) {
            document.getElementById('agent-id').value = currentAgentId || '';
            document.getElementById('agent-id').disabled = currentMode === 'edit';
            document.getElementById('agent-name').value = agentInfo.name || '';
            document.getElementById('agent-description').value = agentInfo.description || '';
            document.getElementById('agent-avatar').value = agentInfo.avatar || '👤';
            
            // Set model dropdown
            const modelSelect = document.getElementById('agent-model');
            for (let i = 0; i < modelSelect.options.length; i++) {
                if (modelSelect.options[i].value === agentInfo.model) {
                    modelSelect.selectedIndex = i;
                    break;
                }
            }
            
            // Set temperature slider
            const temperatureInput = document.getElementById('agent-temperature');
            temperatureInput.value = agentInfo.temperature || 0.7;
            document.getElementById('temp-value').textContent = temperatureInput.value;
            
            // Set specialties
            if (agentInfo.specialties) {
                document.getElementById('agent-specialties').value = 
                    Array.isArray(agentInfo.specialties) ? agentInfo.specialties.join(', ') : agentInfo.specialties;
            } else {
                document.getElementById('agent-specialties').value = '';
            }
            
            document.getElementById('agent-style').value = agentInfo.style || '';
            document.getElementById('agent-prompt').value = agentInfo.systemPrompt || '';
            document.getElementById('agent-greeting').value = agentInfo.greeting || '';
            
            // Show/hide delete button based on mode and agent
            document.getElementById('delete-agent').style.display = 
                (currentMode === 'edit' && currentAgentId !== 'claude') ? 'block' : 'none';
        }
        
        // Reset the agent form for creating a new agent
        function resetAgentForm() {
            document.getElementById('agent-id').value = '';
            document.getElementById('agent-id').disabled = false;
            document.getElementById('agent-name').value = '';
            document.getElementById('agent-description').value = '';
            document.getElementById('agent-avatar').value = '👤';
            document.getElementById('agent-model').selectedIndex = 0;
            document.getElementById('agent-temperature').value = 0.7;
            document.getElementById('temp-value').textContent = '0.7';
            document.getElementById('agent-specialties').value = '';
            document.getElementById('agent-style').value = '';
            document.getElementById('agent-prompt').value = '';
            document.getElementById('agent-greeting').value = '';
            document.getElementById('delete-agent').style.display = 'none';
        }
        
        // Save agent configuration to server
        function saveAgent() {
            const agentId = document.getElementById('agent-id').value.trim();
            
            if (!agentId) {
                alert('Agent ID is required');
                return;
            }
            
            const name = document.getElementById('agent-name').value.trim();
            if (!name) {
                alert('Agent name is required');
                return;
            }
            
            const systemPrompt = document.getElementById('agent-prompt').value.trim();
            if (!systemPrompt) {
                alert('System prompt is required');
                return;
            }
            
            // Prepare agent config
            const agentConfig = {
                id: agentId,
                name: name,
                description: document.getElementById('agent-description').value.trim(),
                avatar: document.getElementById('agent-avatar').value.trim() || '👤',
                model: document.getElementById('agent-model').value,
                temperature: parseFloat(document.getElementById('agent-temperature').value),
                specialties: document.getElementById('agent-specialties').value.split(',').map(s => s.trim()).filter(s => s),
                style: document.getElementById('agent-style').value.trim(),
                system_prompt: systemPrompt,
                greeting: document.getElementById('agent-greeting').value.trim() || `Hello! I'm ${name}. How can I assist you today?`
            };
            
            // Create JSON string from config
            const configJson = JSON.stringify(agentConfig, null, 2);
            
            let apiEndpoint;
            if (currentMode === 'new') {
                apiEndpoint = `/api?message=/create_agent ${encodeURIComponent(configJson)}`;
            } else {
                apiEndpoint = `/api?message=/update_agent ${agentId} ${encodeURIComponent(configJson)}`;
            }
            
            fetch(apiEndpoint)
                .then(response => response.text())
                .then(data => {
                    // If operation was successful
                    if (data.includes('Created agent') || data.includes('Updated agent')) {
                        // Show success message
                        alert(data);
                        
                        // Refresh agent list
                        fetchAgents().then(() => {
                            // Switch to the newly created/updated agent
                            switchToAgent(agentId);
                        });
                    } else {
                        // Show error message
                        alert(`Error: ${data}`);
                    }
                })
                .catch(error => {
                    console.error('Error saving agent:', error);
                    alert(`Error saving agent: ${error.message}`);
                });
        }
        
        // Delete an agent
        function deleteAgent() {
            if (currentAgentId === 'claude') {
                alert('Cannot delete the default agent');
                return;
            }
            
            if (!confirm(`Are you sure you want to delete the agent "${currentAgentId}"?`)) {
                return;
            }
            
            fetch(`/api?message=/delete_agent ${currentAgentId}`)
                .then(response => response.text())
                .then(data => {
                    // If operation was successful
                    if (data.includes('Deleted agent')) {
                        // Show success message
                        alert(data);
                        
                        // Refresh agent list
                        fetchAgents();
                        
                        // Reset form and close panel
                        resetAgentForm();
                        closeAgentPanel();
                    } else {
                        // Show error message
                        alert(`Error: ${data}`);
                    }
                })
                .catch(error => {
                    console.error('Error deleting agent:', error);
                    alert(`Error deleting agent: ${error.message}`);
                });
        }
        
        // Switch to a different agent
        function switchToAgent(agentId) {
            fetch(`/api?message=/agent ${agentId}`)
                .then(response => response.text())
                .then(data => {
                    // If operation was successful
                    if (data.includes('Switched to agent')) {
                        // Show success message in chat
                        const chat = document.getElementById('chat');
                        const systemDiv = document.createElement('div');
                        systemDiv.className = 'message claude';
                        systemDiv.innerHTML = `<strong>System:</strong> ${data}`;
                        chat.appendChild(systemDiv);
                        chat.scrollTop = chat.scrollHeight;
                        
                        // Update current agent ID
                        currentAgentId = agentId;
                        
                        // Refresh agent list
                        fetchAgents();
                    }
                })
                .catch(error => {
                    console.error('Error switching agent:', error);
                    alert(`Error switching agent: ${error.message}`);
                });
        }
        
        // Open the agent configuration panel
        function openAgentPanel() {
            const panel = document.getElementById('agent-config-panel');
            panel.style.display = 'block';
            setTimeout(() => {
                panel.classList.add('visible');
            }, 10);
            
            // Fetch agent list
            fetchAgents()
                .then(() => {
                    // Default to viewing current agent
                    viewCurrentAgent();
                });
        }
        
        // Close the agent configuration panel
        function closeAgentPanel() {
            const panel = document.getElementById('agent-config-panel');
            panel.classList.remove('visible');
            setTimeout(() => {
                panel.style.display = 'none';
            }, 300);
        }
        
        // View the currently selected agent
        function viewCurrentAgent() {
            const select = document.getElementById('current-agent');
            const agentId = select.value;
            currentAgentId = agentId;
            currentMode = 'edit';
            
            fetchAgentInfo(agentId);
        }
        
        // Handle send message
        function sendMessage() {
            const input = document.getElementById('message');
            const message = input.value.trim();
            
            if (message === '') return;
            
            // Display user message
            const chat = document.getElementById('chat');
            const userDiv = document.createElement('div');
            userDiv.className = 'message user';
            userDiv.innerHTML = '<strong>You:</strong> ' + message;
            chat.appendChild(userDiv);
            
            // Clear input
            input.value = '';
            
            // Show thinking message
            const thinkingDiv = document.createElement('div');
            thinkingDiv.className = 'message claude thinking';
            thinkingDiv.id = 'thinking';
            thinkingDiv.textContent = 'Claude is thinking...';
            chat.appendChild(thinkingDiv);
            chat.scrollTop = chat.scrollHeight;
            
            // Send to server
            fetch('/api?message=' + encodeURIComponent(message))
                .then(response => response.text())
                .then(data => {
                    // Remove thinking message
                    const thinking = document.getElementById('thinking');
                    if (thinking) thinking.remove();
                    
                    // Display Claude's response
                    const claudeDiv = document.createElement('div');
                    claudeDiv.className = 'message claude';
                    
                    // Format response with code blocks if they exist
                    const formattedResponse = formatCodeBlocks(data);
                    claudeDiv.innerHTML = '<strong>Claude:</strong> ' + formattedResponse;
                    
                    chat.appendChild(claudeDiv);
                    chat.scrollTop = chat.scrollHeight;
                })
                .catch(error => {
                    console.error('Error:', error);
                    const thinking = document.getElementById('thinking');
                    if (thinking) {
                        thinking.className = 'message claude';
                        thinking.innerHTML = '<strong>Claude:</strong> Error communicating with the server: ' + error;
                    }
                });
        }
        
        // Initialize on document load
        document.addEventListener('DOMContentLoaded', function() {
            // Set up theme toggle button
            document.getElementById('theme-toggle').addEventListener('click', toggleTheme);
            
            // Initialize theme from localStorage or default to light
            const savedTheme = localStorage.getItem('theme');
            if (savedTheme) {
                setTheme(savedTheme);
            }
            
            // Set up agent panel buttons
            document.getElementById('open-agent-panel').addEventListener('click', openAgentPanel);
            document.getElementById('close-agent-panel').addEventListener('click', closeAgentPanel);
            document.getElementById('view-agent').addEventListener('click', viewCurrentAgent);
            
            document.getElementById('new-agent').addEventListener('click', function() {
                currentMode = 'new';
                resetAgentForm();
            });
            
            document.getElementById('save-agent').addEventListener('click', saveAgent);
            document.getElementById('delete-agent').addEventListener('click', deleteAgent);
            document.getElementById('cancel-agent').addEventListener('click', closeAgentPanel);
            
            // Set up temperature slider
            const temperatureSlider = document.getElementById('agent-temperature');
            const tempValue = document.getElementById('temp-value');
            temperatureSlider.addEventListener('input', function() {
                tempValue.textContent = this.value;
            });
            
            // Auto-focus message input
            document.getElementById('message').focus();
        });
        
        // Handle Enter key for sending messages
        document.getElementById('message').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    </script>
</body>
</html>
"""

# Import search functionality
from search import search_conversations, format_search_results, search_current_conversation

# Import domain-specific prompts
from prompts import get_available_domains, initialize_prompts_directory, create_custom_domain, delete_domain

# Import settings management
from settings import initialize_settings, get_setting, update_setting, format_settings_display, reset_to_defaults

# Import code analysis tools
from code_analyzer import analyze_code, analyze_directory, format_analysis_report

# Import export/import functionality
from export_import import export_conversation, export_all_formats, import_conversation, EXPORT_FORMATS

# Import offline mode functionality
from offline_mode import initialize_cache, get_connection_status, call_claude_with_fallback, offline_command

# Import agent switching framework
from agents import (
    initialize_agents, get_agent_config, set_current_agent, get_current_agent_id,
    get_available_agents, create_agent, update_agent, delete_agent,
    get_system_prompt, get_greeting, get_agent_model, format_agent_info
)

# Initialize prompts directory
initialize_prompts_directory()

# Initialize settings
settings = initialize_settings()

# Initialize agent switching framework
initialize_agents()

# Initialize cache for offline mode
initialize_cache()

# Check connection status
is_online = get_connection_status()
if not is_online:
    logger.warning("Running in offline mode - API connection not available")
elif not API_KEY:
    logger.warning("Running in offline mode - API key not available")

# Create a custom HTTP request handler
class TheEngineerHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            
            # Serve the main page
            if parsed_path.path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(HTML.encode())
                return
                
            # Handle API requests
            elif parsed_path.path.startswith('/api'):
                query = urllib.parse.parse_qs(parsed_path.query)
                message = query.get('message', [''])[0]
                
                if message.startswith('/'):
                    # Handle commands
                    if message == '/save':
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"conversation_{timestamp}.json"
                        with open(os.path.join(CONVERSATION_DIR, filename), 'w') as f:
                            json.dump(conversation_history, f, indent=2)
                        response = f"Conversation saved as {filename}"
                    elif message == '/list':
                        conversations = list_saved_conversations()
                        if conversations:
                            response = "Saved conversations:\n" + "\n".join([f"{i+1}. {c}" for i, c in enumerate(conversations)])
                        else:
                            response = "No saved conversations found."
                    elif message == '/clear':
                        conversation_history.clear()
                        response = "Conversation history cleared."
                    elif message.startswith('/search'):
                        # Format: /search query
                        # or: /search saved query (to search saved conversations)
                        parts = message[8:].strip().split(' ', 1)
                        
                        if not parts[0]:
                            response = "Usage: /search <query> - Searches current conversation\n" + \
                                      "/search saved <query> - Searches all saved conversations"
                        elif parts[0].lower() == 'saved' and len(parts) > 1:
                            # Search saved conversations
                            query = parts[1]
                            results = search_conversations(query, CONVERSATION_DIR)
                            response = format_search_results(results)
                        else:
                            # Search current conversation
                            query = parts[0] if len(parts) == 1 else message[8:].strip()
                            response = search_current_conversation(query, conversation_history)
                    
                    elif message == '/domains':
                        # List available domains
                        domains = get_available_domains()
                        if current_domain:
                            response = f"Current domain: {current_domain}\n\nAvailable domains:\n" + \
                                      "\n".join([f"• {domain}" for domain in domains])
                        else:
                            response = f"Current domain: default\n\nAvailable domains:\n" + \
                                      "\n".join([f"• {domain}" for domain in domains])
                    
                    elif message.startswith('/domain '):
                        # Format: /domain [domain_name]
                        # Or: /domain default (to reset to default)
                        domain = message[8:].strip()
                        
                        if not domain:
                            response = "Usage: /domain <domain_name> - Sets the active domain\n" + \
                                      "/domain default - Resets to the default domain"
                        elif domain.lower() == 'default':
                            global current_domain
                            current_domain = None
                            update_setting('domain', None)
                            response = "Reset to default domain."
                        else:
                            domains = get_available_domains()
                            if domain in domains:
                                current_domain = domain
                                update_setting('domain', domain)
                                response = f"Switched to {domain} domain."
                            else:
                                response = f"Domain '{domain}' not found. Available domains:\n" + \
                                          "\n".join([f"• {d}" for d in domains])
                    
                    elif message.startswith('/create_domain '):
                        # Format: /create_domain domain_name prompt
                        parts = message[15:].strip().split(' ', 1)
                        
                        if len(parts) < 2:
                            response = "Usage: /create_domain <domain_name> <prompt>"
                        else:
                            domain_name = parts[0]
                            prompt = parts[1]
                            
                            if create_custom_domain(domain_name, prompt):
                                response = f"Created custom domain: {domain_name}"
                            else:
                                response = f"Failed to create domain: {domain_name}. Use only letters, numbers, and underscores for domain name."
                    
                    elif message == '/settings':
                        # Display current settings
                        response = format_settings_display()
                    
                    elif message.startswith('/setting '):
                        # Format: /setting key value
                        parts = message[9:].strip().split(' ', 1)
                        
                        if len(parts) < 2:
                            response = "Usage: /setting <key> <value>"
                        else:
                            key = parts[0]
                            value = parts[1]
                            
                            # Handle special values
                            if value.lower() == 'true':
                                value = True
                            elif value.lower() == 'false':
                                value = False
                            elif value.lower() == 'null' or value.lower() == 'none':
                                value = None
                            elif value.isdigit():
                                value = int(value)
                            
                            if update_setting(key, value):
                                response = f"Updated setting: {key} = {value}"
                            else:
                                response = f"Failed to update setting: {key}"
                    
                    elif message == '/reset_settings':
                        # Reset all settings to defaults
                        if reset_to_defaults():
                            response = "All settings reset to defaults."
                        else:
                            response = "Failed to reset settings."
                    
                    elif message.startswith('/export'):
                        # Format: /export [format]
                        # Format options: json, txt, md, html, csv, all
                        parts = message[8:].strip().split()
                        format = parts[0].lower() if parts else 'json'
                        
                        if not conversation_history:
                            response = "No conversation to export."
                        elif format == 'all':
                            # Export in all formats
                            try:
                                zip_path = export_all_formats(conversation_history)
                                response = f"Conversation exported to all formats: {zip_path}"
                            except Exception as e:
                                response = f"Error exporting conversation: {str(e)}"
                        elif format in EXPORT_FORMATS:
                            # Export in specified format
                            try:
                                export_path = export_conversation(conversation_history, format)
                                response = f"Conversation exported as {format}: {export_path}"
                            except Exception as e:
                                response = f"Error exporting conversation: {str(e)}"
                        else:
                            response = f"Invalid export format: {format}. Available formats: " + \
                                      ", ".join(EXPORT_FORMATS) + ", all"
                    
                    elif message.startswith('/import'):
                        # Format: /import [filepath]
                        parts = message[8:].strip().split()
                        
                        if not parts:
                            response = "Usage: /import <filepath>"
                        else:
                            filepath = parts[0]
                            
                            try:
                                imported_conversation = import_conversation(filepath)
                                if isinstance(imported_conversation, list):
                                    # Clear current conversation if not empty
                                    if conversation_history:
                                        conversation_history.clear()
                                    
                                    # Add imported messages
                                    conversation_history.extend(imported_conversation)
                                    response = f"Conversation imported successfully: {len(imported_conversation)} messages"
                                else:
                                    response = imported_conversation  # Error message
                            except Exception as e:
                                response = f"Error importing conversation: {str(e)}"
                    
                    elif message.startswith('/agents'):
                        # List available agents
                        agents = get_available_agents()
                        response = "Available agents:\n"
                        
                        for agent in agents:
                            if agent.get("is_current", False):
                                response += f"• {agent['avatar']} **{agent['name']}** (ID: {agent['id']}) - _current agent_\n"
                            else:
                                response += f"• {agent['avatar']} **{agent['name']}** (ID: {agent['id']})\n"
                                
                            if agent.get("description"):
                                response += f"  {agent['description']}\n"
                                
                            if agent.get("specialties"):
                                response += f"  Specialties: {', '.join(agent['specialties'])}\n"
                                
                            response += "\n"
                        
                        response += "\nTo switch agents, use: `/agent <id>`\nTo view agent details, use: `/agent_info <id>`"
                    
                    elif message.startswith('/agent '):
                        # Format: /agent <agent_id>
                        agent_id = message[7:].strip()
                        
                        if not agent_id:
                            response = "Usage: /agent <agent_id> - Switches to the specified agent"
                        else:
                            success, result = set_current_agent(agent_id)
                            if success:
                                response = result
                            else:
                                response = result
                    
                    elif message.startswith('/agent_info'):
                        # Format: /agent_info [agent_id]
                        agent_id = message[11:].strip() if len(message) > 11 else None
                        
                        response = format_agent_info(agent_id)
                    
                    elif message.startswith('/create_agent'):
                        # Format: /create_agent <json_config>
                        config_json = message[13:].strip()
                        
                        if not config_json:
                            response = "Usage: /create_agent <json_config> - Creates a new agent with the specified configuration"
                        else:
                            try:
                                config = json.loads(config_json)
                                success, result = create_agent(config)
                                response = result
                            except json.JSONDecodeError:
                                response = "Error: Invalid JSON configuration"
                            except Exception as e:
                                response = f"Error creating agent: {str(e)}"
                    
                    elif message.startswith('/update_agent'):
                        # Format: /update_agent <agent_id> <json_config>
                        parts = message[13:].strip().split(' ', 1)
                        
                        if len(parts) < 2:
                            response = "Usage: /update_agent <agent_id> <json_config> - Updates an existing agent"
                        else:
                            agent_id = parts[0]
                            config_json = parts[1]
                            
                            try:
                                updates = json.loads(config_json)
                                success, result = update_agent(agent_id, updates)
                                response = result
                            except json.JSONDecodeError:
                                response = "Error: Invalid JSON configuration"
                            except Exception as e:
                                response = f"Error updating agent: {str(e)}"
                    
                    elif message.startswith('/delete_agent'):
                        # Format: /delete_agent <agent_id>
                        agent_id = message[13:].strip()
                        
                        if not agent_id:
                            response = "Usage: /delete_agent <agent_id> - Deletes the specified agent"
                        else:
                            success, result = delete_agent(agent_id)
                            response = result
                    
                    elif message.startswith('/offline'):
                        # Format: /offline [command] [args]
                        parts = message[9:].strip().split()
                        command = parts[0] if parts else "status"
                        args = parts[1:] if len(parts) > 1 else []
                        
                        if command == "status":
                            # Check connection status
                            online = get_connection_status()
                            response = f"Offline mode status:\n- Connection: {'Online' if online else 'Offline'}\n- API key: {'Available' if API_KEY else 'Not available'}\n- Mode: {'Online' if online and API_KEY else 'Offline'}"
                        else:
                            # Handle other offline commands
                            response = offline_command(command, *args)
                    elif message.startswith('/projects'):
                        projects = get_replit_projects()
                        if isinstance(projects, list):
                            response = "Your Replit projects:\n" + "\n".join([f"{i+1}. {p}" for i, p in enumerate(projects)])
                        else:
                            response = projects  # This is an error message
                    elif message.startswith('/files'):
                        # Format: /files ProjectName [path]
                        parts = message[7:].strip().split(' ', 1)
                        
                        # Handle no arguments - use current directory
                        if not parts[0]:
                            project_name = "."
                            path = ""
                        else:
                            project_name = parts[0]
                            path = parts[1] if len(parts) > 1 else ""
                        
                        result = list_project_files(project_name, path)
                        if isinstance(result, dict):
                            response = f"Contents of {project_name}/{result['path']}:\n\n"
                            if result['directories']:
                                response += "Directories:\n" + "\n".join([f"📁 {d}" for d in result['directories']]) + "\n\n"
                            if result['files']:
                                response += "Files:\n" + "\n".join([f"📄 {f}" for f in result['files']])
                            if not result['directories'] and not result['files']:
                                response += "Directory is empty."
                        else:
                            response = result  # This is an error message
                    elif message.startswith('/read'):
                        # Format: /read ProjectName FilePath
                        parts = message[6:].strip().split(' ', 1)
                        
                        # Handle different formats
                        if not parts[0]:
                            response = "Usage: /read [project] [file]"
                        elif len(parts) < 2:
                            response = "Please specify a file path"
                        else:
                            project_name = parts[0]
                            file_path = parts[1]
                            content = read_file(project_name, file_path)
                            response = f"Content of {project_name}/{file_path}:\n\n```\n{content}\n```"
                    elif message.startswith('/analyze'):
                        # Format: /analyze ProjectName [FilePath or pattern]
                        parts = message[9:].strip().split(' ', 1)
                        
                        # Handle different formats
                        if not parts[0]:
                            response = "Usage: /analyze [project] [pattern]"
                            self.send_response(200)
                            self.send_header('Content-type', 'text/plain; charset=utf-8')
                            self.end_headers()
                            self.wfile.write(response.encode('utf-8'))
                            return
                            
                        project_name = parts[0]
                        file_pattern = parts[1] if len(parts) > 1 else "*.py"
                        
                        try:
                            # Find matching files
                            matching_files = find_files(project_name, file_pattern)
                            
                            if not matching_files:
                                response = f"No files matching '{file_pattern}' found in {project_name}"
                            elif isinstance(matching_files, str) and matching_files.startswith("Error"):
                                response = matching_files
                            else:
                                # Create a context with file contents for Claude to analyze
                                context = f"Project: {project_name}\nFiles to analyze:\n\n"
                                for file_path in matching_files[:5]:  # Limit to 5 files to avoid overloading
                                    content = read_file(project_name, file_path)
                                    if isinstance(content, str) and content.startswith("Error"):
                                        context += f"--- FILE: {file_path} ---\nError reading file: {content}\n\n"
                                    else:
                                        # Truncate very large files
                                        if len(content) > 10000:
                                            display_content = content[:10000] + "\n... [File truncated due to size] ...\n"
                                        else:
                                            display_content = content
                                        
                                        context += f"--- FILE: {file_path} ---\n{display_content}\n\n"
                                
                                # Add a note if there were more files
                                if len(matching_files) > 5:
                                    context += f"\nNote: Found {len(matching_files)} matching files, but only showing the first 5 for analysis."
                                
                                # Use enhanced code analyzer for initial analysis
                                detailed_analysis = "# Code Analysis Report\n\n"
                                
                                for file_path in matching_files[:5]:
                                    content = read_file(project_name, file_path)
                                    if isinstance(content, str) and not content.startswith("Error"):
                                        full_path = os.path.join(project_name, file_path)
                                        try:
                                            # Generate analysis report for this file
                                            analysis = analyze_code(content, file_path)
                                            detailed_analysis += format_analysis_report(analysis, file_path) + "\n\n"
                                        except Exception as e:
                                            logger.error(f"Error analyzing file {file_path}: {str(e)}")
                                            detailed_analysis += f"Error analyzing {file_path}: {str(e)}\n\n"
                                
                                # Send to Claude with enhanced analysis and context
                                analysis_prompt = f"Please analyze these files from project {project_name}. " \
                                                f"I've provided an initial code analysis below.\n\n" \
                                                f"Review this analysis and provide additional insights on: " \
                                                f"code quality, patterns, security, maintainability, and performance.\n\n" \
                                                f"Focus on providing specific, actionable recommendations that would most " \
                                                f"improve this codebase. Include examples where helpful."
                                
                                analysis_result, _ = call_claude(context + "\n" + detailed_analysis + "\n\n" + analysis_prompt, conversation_history)
                                
                                # Combine automated analysis with Claude's insights
                                response = "## Automated Code Analysis\n\n" + detailed_analysis + "\n\n## Claude's Analysis\n\n" + analysis_result
                        except Exception as e:
                            logger.error(f"Error analyzing files: {str(e)}")
                            response = f"Error analyzing files: {str(e)}"
                    else:
                        response = "Unknown command. Available commands: /save, /list, /clear, /projects, /files, /read, /analyze"
                else:
                    # Process regular messages
                    response, conversation_history = call_claude(message, conversation_history)
                
                self.send_response(200)
                self.send_header('Content-type', 'text/plain; charset=utf-8')
                self.end_headers()
                self.wfile.write(response.encode('utf-8'))
                return
                
            # Serve any other path as 404
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
            
        except Exception as e:
            logger.error(f"Error handling request: {str(e)}")
            self.send_response(500)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Server error: {str(e)}".encode())
    
    def log_message(self, format, *args):
        """Override to use our logger instead of printing to stderr"""
        logger.info("%s - %s" % (self.address_string(), format % args))

def run_web_server():
    """Run the HTTP server"""
    port = 8080
    handler = TheEngineerHandler
    
    try:
        httpd = socketserver.TCPServer(("", port), handler)
        logger.info(f"Web server running at http://localhost:{port}")
        print(f"The Engineer web interface running at http://localhost:{port}")
        print("Open the Preview tab to interact with the web interface")
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Web server stopped by user")
        print("Web server stopped")
    except Exception as e:
        logger.error(f"Web server error: {str(e)}")
        print(f"Error starting web server: {str(e)}")

def run_console():
    """Run the original console interface"""
    global conversation_history
    
    print("\n\033[1;32m=== The Engineer Terminal ===\033[0m")
    print("You are now connected to your specific Claude instance.")
    print("\nAvailable commands:")
    print("  \033[1msave [filename]\033[0m - Save conversation (optional custom filename)")
    print("  \033[1mlist\033[0m - List saved conversations")
    print("  \033[1mload <number>\033[0m - Load conversation by number")
    print("  \033[1mexport [format]\033[0m - Export conversation (json, txt, md, html, csv, all)")
    print("  \033[1mimport <filepath>\033[0m - Import conversation from file")
    print("  \033[1mhistory\033[0m - Show conversation history")
    print("  \033[1msearch <query>\033[0m - Search current conversation")
    print("  \033[1msearch saved <query>\033[0m - Search all saved conversations")
    print("  \033[1magents\033[0m - List available agent personalities")
    print("  \033[1magent <id>\033[0m - Switch to a specific agent")
    print("  \033[1magent_info [id]\033[0m - View agent details")
    print("  \033[1mdomains\033[0m - List available domain prompts")
    print("  \033[1mdomain <name>\033[0m - Switch to a specific domain")
    print("  \033[1mdomain default\033[0m - Reset to default domain")
    print("  \033[1msettings\033[0m - View all current settings")
    print("  \033[1msetting <key> <value>\033[0m - Update a specific setting")
    print("  \033[1mreset_settings\033[0m - Reset all settings to defaults")
    print("  \033[1moffline\033[0m - Show offline mode status")
    print("  \033[1moffline <command>\033[0m - Run offline command (cache_status, clear_cache, add_response)")
    print("  \033[1mclear\033[0m - Clear current conversation")
    print("  \033[1mexit\033[0m - Exit the application")
    print("  \033[1mprojects\033[0m - List all your Replit projects")
    print("  \033[1mfiles [project]\033[0m - List files in a project")
    print("  \033[1mread [project] [file]\033[0m - View file contents")
    print("  \033[1manalyze [project] [pattern]\033[0m - Analyze files")
    print("  \033[1mweb\033[0m - Switch to web interface mode")
    
    while True:
        # Get user input
        try:
            user_input = input("\n\033[1mYou:\033[0m ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break
        
        # Check for special commands
        if user_input.lower() == "exit":
            print("Goodbye!")
            break
            
        elif user_input.lower() == "web":
            print("\nSwitching to web interface mode...")
            run_web_server()
            break
            
        elif user_input.lower().startswith("save"):
            parts = user_input.split(maxsplit=1)
            filename = parts[1] if len(parts) > 1 else None
            if filename and not filename.endswith(".json"):
                filename += ".json"
                
            saved_path = save_conversation(conversation_history, filename)
            print(f"Conversation saved to {saved_path}")
            continue
            
        elif user_input.lower() == "list":
            conversations = list_saved_conversations()
            if conversations:
                print("\nSaved conversations:")
                for i, conv in enumerate(conversations, 1):
                    print(f"  {i}. {conv}")
            else:
                print("\nNo saved conversations found.")
            continue
            
        elif user_input.lower().startswith("load "):
            try:
                idx = int(user_input.split()[1]) - 1
                conversations = list_saved_conversations()
                if 0 <= idx < len(conversations):
                    loaded_conversation = load_conversation(conversations[idx])
                    if loaded_conversation:
                        conversation_history = loaded_conversation
                        print(f"\nLoaded conversation from {conversations[idx]}")
                        display_history(conversation_history[-3:])  # Show last few messages
                    else:
                        print("\nError loading conversation.")
                else:
                    print("\nInvalid conversation number.")
            except (ValueError, IndexError) as e:
                print(f"\nError loading conversation: {str(e)}")
            continue
            
        elif user_input.lower() == "history":
            display_history(conversation_history)
            continue
            
        elif user_input.lower() == "clear":
            conversation_history.clear()
            print("\nConversation history cleared.")
            continue
        
        # Search commands
        elif user_input.lower().startswith("search "):
            parts = user_input[7:].strip().split(' ', 1)
            
            if not parts[0]:
                print("\nUsage: search <query> - Searches current conversation")
                print("       search saved <query> - Searches all saved conversations")
                continue
                
            if parts[0].lower() == 'saved' and len(parts) > 1:
                # Search saved conversations
                query = parts[1]
                print(f"\nSearching saved conversations for '{query}'...\n")
                results = search_conversations(query, CONVERSATION_DIR)
                print(format_search_results(results))
            else:
                # Search current conversation
                query = parts[0] if len(parts) == 1 else user_input[7:].strip()
                print(f"\nSearching current conversation for '{query}'...\n")
                print(search_current_conversation(query, conversation_history))
            continue
        
        # Agent commands
        elif user_input.lower() == "agents":
            agents = get_available_agents()
            print("\nAvailable agents:")
            
            for agent in agents:
                if agent.get("is_current", False):
                    print(f"\n{agent['avatar']} \033[1m{agent['name']}\033[0m (ID: {agent['id']}) - \033[1;34mcurrent agent\033[0m")
                else:
                    print(f"\n{agent['avatar']} \033[1m{agent['name']}\033[0m (ID: {agent['id']})")
                
                if agent.get("description"):
                    print(f"  Description: {agent['description']}")
                
                if agent.get("specialties"):
                    print(f"  Specialties: {', '.join(agent['specialties'])}")
            
            print("\nTo switch agents, use: agent <id>")
            print("To view agent details, use: agent_info [id]")
            continue
        
        elif user_input.lower().startswith("agent_info"):
            parts = user_input.split(maxsplit=1)
            agent_id = parts[1] if len(parts) > 1 else None
            
            info = format_agent_info(agent_id)
            print(f"\n{info}")
            continue
        
        elif user_input.lower().startswith("agent "):
            agent_id = user_input[6:].strip()
            
            if not agent_id:
                print("\nUsage: agent <agent_id> - Switches to the specified agent")
                continue
                
            success, result = set_current_agent(agent_id)
            print(f"\n{result}")
            continue
        
        # Domain commands
        elif user_input.lower() == "domains":
            domains = get_available_domains()
            print("\nAvailable domains:")
            for i, domain in enumerate(domains, 1):
                if domain == current_domain:
                    print(f"  {i}. {domain} (active)")
                else:
                    print(f"  {i}. {domain}")
            
            if current_domain is None:
                print("\nCurrent domain: default")
            else:
                print(f"\nCurrent domain: {current_domain}")
            continue
            
        elif user_input.lower().startswith("domain "):
            domain = user_input[7:].strip()
            
            if domain.lower() == 'default':
                global current_domain
                current_domain = None
                update_setting('domain', None)
                print("\nReset to default domain.")
            else:
                domains = get_available_domains()
                if domain in domains:
                    global current_domain
                    current_domain = domain
                    update_setting('domain', domain)
                    print(f"\nSwitched to {domain} domain.")
                else:
                    print(f"\nDomain '{domain}' not found. Available domains:")
                    for i, d in enumerate(domains, 1):
                        print(f"  {i}. {d}")
            continue
            
        # Settings commands
        elif user_input.lower() == "settings":
            print("\n" + format_settings_display())
            continue
            
        elif user_input.lower().startswith("setting "):
            parts = user_input[8:].strip().split(' ', 1)
            
            if len(parts) < 2:
                print("\nUsage: setting <key> <value>")
                continue
                
            key = parts[0]
            value = parts[1]
            
            # Handle special values
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            elif value.lower() == 'null' or value.lower() == 'none':
                value = None
            elif value.isdigit():
                value = int(value)
            
            if update_setting(key, value):
                print(f"\nUpdated setting: {key} = {value}")
            else:
                print(f"\nFailed to update setting: {key}")
            continue
            
        elif user_input.lower() == "reset_settings":
            if reset_to_defaults():
                print("\nAll settings reset to defaults.")
            else:
                print("\nFailed to reset settings.")
            continue
        
        # Export/Import commands
        elif user_input.lower().startswith("export "):
            format = user_input[7:].strip().lower()
            
            if not conversation_history:
                print("\nNo conversation to export.")
                continue
                
            if format == 'all':
                # Export in all formats
                try:
                    print("\nExporting conversation in all formats...")
                    zip_path = export_all_formats(conversation_history)
                    print(f"\nConversation exported to all formats: {zip_path}")
                except Exception as e:
                    print(f"\nError exporting conversation: {str(e)}")
            elif format in EXPORT_FORMATS:
                # Export in specified format
                try:
                    print(f"\nExporting conversation as {format}...")
                    export_path = export_conversation(conversation_history, format)
                    print(f"\nConversation exported as {format}: {export_path}")
                except Exception as e:
                    print(f"\nError exporting conversation: {str(e)}")
            else:
                print(f"\nInvalid export format: {format}")
                print(f"Available formats: {', '.join(EXPORT_FORMATS)}, all")
            continue
        
        elif user_input.lower().startswith("import "):
            filepath = user_input[7:].strip()
            
            if not filepath:
                print("\nUsage: import <filepath>")
                continue
                
            print(f"\nImporting conversation from {filepath}...")
            try:
                imported_conversation = import_conversation(filepath)
                if isinstance(imported_conversation, list):
                    # Clear current conversation if not empty
                    if conversation_history:
                        conversation_history.clear()
                    
                    # Add imported messages
                    conversation_history.extend(imported_conversation)
                    print(f"\nConversation imported successfully: {len(imported_conversation)} messages")
                else:
                    print(f"\n{imported_conversation}")  # Error message
            except Exception as e:
                print(f"\nError importing conversation: {str(e)}")
            continue
        
        # Offline commands
        elif user_input.lower() == "offline":
            # Show offline status
            online = get_connection_status()
            print(f"\nOffline mode status:")
            print(f"- Connection: {'Online' if online else 'Offline'}")
            print(f"- API key: {'Available' if API_KEY else 'Not available'}")
            print(f"- Mode: {'Online' if online and API_KEY else 'Offline'}")
            continue
            
        elif user_input.lower().startswith("offline "):
            parts = user_input[8:].strip().split()
            command = parts[0] if parts else "status"
            args = parts[1:] if len(parts) > 1 else []
            
            print(f"\n{offline_command(command, *args)}")
            continue
            
        # Project commands
        elif user_input.lower() == "projects":
            projects = get_replit_projects()
            if isinstance(projects, list):
                print("\nYour Replit projects:")
                for i, proj in enumerate(projects, 1):
                    print(f"  {i}. {proj}")
            else:
                print(f"\n{projects}")
            continue
            
        elif user_input.lower().startswith("files "):
            parts = user_input[6:].strip().split(' ', 1)
            project_name = parts[0]
            path = parts[1] if len(parts) > 1 else ""
            
            result = list_project_files(project_name, path)
            if isinstance(result, dict):
                print(f"\nContents of {project_name}/{result['path']}:")
                if result['directories']:
                    print("\nDirectories:")
                    for d in result['directories']:
                        print(f"  📁 {d}")
                if result['files']:
                    print("\nFiles:")
                    for f in result['files']:
                        print(f"  📄 {f}")
                if not result['directories'] and not result['files']:
                    print("\nDirectory is empty.")
            else:
                print(f"\n{result}")
            continue
            
        elif user_input.lower().startswith("read "):
            parts = user_input[5:].strip().split(' ', 1)
            if len(parts) < 2:
                print("\nUsage: read [project] [file]")
                continue
                
            project_name = parts[0]
            file_path = parts[1]
            content = read_file(project_name, file_path)
            
            print(f"\nContent of {project_name}/{file_path}:")
            print("\n" + "="*50)
            print(content)
            print("="*50)
            continue
            
        elif user_input.lower().startswith("analyze "):
            parts = user_input[8:].strip().split(' ', 1)
            if not parts[0]:
                print("\nUsage: analyze [project] [pattern]")
                continue
                
            project_name = parts[0]
            file_pattern = parts[1] if len(parts) > 1 else "*.py"
            
            try:
                # Find matching files
                matching_files = find_files(project_name, file_pattern)
                
                if not matching_files:
                    print(f"\nNo files matching '{file_pattern}' found in {project_name}")
                    continue
                    
                if isinstance(matching_files, str) and matching_files.startswith("Error"):
                    print(f"\n{matching_files}")
                    continue
                
                print(f"\nFound {len(matching_files)} files matching '{file_pattern}' in {project_name}")
                print("Analyzing files with Claude...\n")
                
                # Create a context with file contents for Claude to analyze
                context = f"Project: {project_name}\nFiles to analyze:\n\n"
                for file_path in matching_files[:5]:  # Limit to 5 files
                    content = read_file(project_name, file_path)
                    if isinstance(content, str) and content.startswith("Error"):
                        context += f"--- FILE: {file_path} ---\nError reading file: {content}\n\n"
                    else:
                        # Truncate very large files
                        if len(content) > 10000:
                            display_content = content[:10000] + "\n... [File truncated due to size] ...\n"
                        else:
                            display_content = content
                        
                        context += f"--- FILE: {file_path} ---\n{display_content}\n\n"
                
                # Add a note if there were more files
                if len(matching_files) > 5:
                    context += f"\nNote: Found {len(matching_files)} matching files, but only showing the first 5 for analysis."
                
                # Use enhanced code analyzer for initial analysis
                print("\033[3mRunning automated code analysis...\033[0m")
                detailed_analysis = "# Code Analysis Report\n\n"
                
                for file_path in matching_files[:5]:
                    content = read_file(project_name, file_path)
                    if isinstance(content, str) and not content.startswith("Error"):
                        full_path = os.path.join(project_name, file_path)
                        try:
                            # Generate analysis report for this file
                            analysis = analyze_code(content, file_path)
                            file_report = format_analysis_report(analysis, file_path)
                            detailed_analysis += file_report + "\n\n"
                            
                            # Print a summary of the analysis
                            print(f"\n\033[1mAnalyzed {file_path}:\033[0m")
                            issues = len(analysis['patterns']['issues'])
                            warnings = len(analysis['patterns']['warnings'])
                            practices = len(analysis['patterns']['good_practices'])
                            print(f"  • {issues} issues, {warnings} warnings, {practices} good practices identified")
                        except Exception as e:
                            print(f"\n\033[1;31mError analyzing {file_path}: {str(e)}\033[0m")
                            detailed_analysis += f"Error analyzing {file_path}: {str(e)}\n\n"
                
                # Send to Claude with enhanced analysis and context
                analysis_prompt = f"Please analyze these files from project {project_name}. " \
                                f"I've provided an initial code analysis below.\n\n" \
                                f"Review this analysis and provide additional insights on: " \
                                f"code quality, patterns, security, maintainability, and performance.\n\n" \
                                f"Focus on providing specific, actionable recommendations that would most " \
                                f"improve this codebase. Include examples where helpful."
                
                print("\n\033[3mSending to Claude for additional insights...\033[0m")
                analysis_result, conversation_history = call_claude(context + "\n" + detailed_analysis + "\n\n" + analysis_prompt, conversation_history)
                
                # Display the analysis
                print(f"\n\033[1;34m=== Automated Code Analysis ===\033[0m")
                print(detailed_analysis)
                print(f"\n\033[1;34m=== Claude's Analysis ===\033[0m")
                print(analysis_result)
            except Exception as e:
                print(f"\nError analyzing files: {str(e)}")
            continue
        
        # Call Claude and get response
        print("\n\033[3mClaude is thinking...\033[0m")
        try:
            response, conversation_history = call_claude(user_input, conversation_history)
            print(f"\n\033[1;34mClaude:\033[0m {response}")
        except Exception as e:
            print(f"\033[1;31mError communicating with Claude: {str(e)}\033[0m")

if __name__ == "__main__":
    # Choose mode based on environment or command line args
    import sys
    
    # Create welcome message
    print("""
  ______      __           __  __  _           __    ___   ____
 / ____/___  / /_  ____   /  |/  |(_)____   __/ /   /   | / __ \\ 
/ __/ / __ \\/ __ \\/ __ \\ / /|_/ // // __ \\ / / /   / /| |/ /_/ /
/ /___/ /_/ / / / / /_/ // /  / // // / / // / /___/ ___ / _, _/ 
\\____/\\____/_/ /_/\\____//_/  /_//_//_/ /_//_/_____/_/  |_/_/ |_|  
                                                                    
    """)
    
    # Check if run with --web flag
    if len(sys.argv) > 1 and sys.argv[1] == '--web':
        run_web_server()
    else:
        # Check if running in a non-interactive environment
        import os
        if os.environ.get('REPLIT_ENVIRONMENT') == '1' or not sys.stdin.isatty():
            # Auto-select web interface in Replit environment
            print("Auto-selecting web interface for non-interactive environment")
            run_web_server()
        else:
            # Ask user which interface to use
            print("\nChoose interface mode:")
            print("1. Console Interface (original)")
            print("2. Web Interface (new)")
            
            try:
                choice = input("\nEnter choice (1 or 2): ").strip()
                if choice == "2":
                    run_web_server()
                else:
                    # Default to console mode
                    run_console()
            except (KeyboardInterrupt, EOFError):
                print("\nExiting...")
                sys.exit(0)