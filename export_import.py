"""
Export and import functionality for The Engineer conversations.

This module provides functions to export conversations in various formats
and import conversations from exported files.
"""

import os
import json
import zipfile
import logging
import time
import markdown
import csv
from typing import Dict, List, Any, Optional, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Directory for exported conversations
EXPORT_DIR = "exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

# Available export formats
EXPORT_FORMATS = ["json", "txt", "md", "html", "csv"]

def export_conversation(conversation: List[Dict[str, str]], format: str = "json", filename: Optional[str] = None, include_metadata: bool = True) -> str:
    """Export a conversation in the specified format"""
    try:
        # Create exports directory if it doesn't exist
        os.makedirs(EXPORT_DIR, exist_ok=True)
        
        # Generate filename if not provided
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_{timestamp}.{format}"
        elif not filename.endswith(f".{format}"):
            filename = f"{filename}.{format}"
            
        # Full path to the export file
        export_path = os.path.join(EXPORT_DIR, filename)
        
        # Export in the specified format
        if format == "json":
            export_json(conversation, export_path, include_metadata)
        elif format == "txt":
            export_text(conversation, export_path)
        elif format == "md":
            export_markdown(conversation, export_path)
        elif format == "html":
            export_html(conversation, export_path)
        elif format == "csv":
            export_csv(conversation, export_path)
        else:
            raise ValueError(f"Unsupported export format: {format}")
            
        logger.info(f"Conversation exported as {format}: {export_path}")
        return export_path
    
    except Exception as e:
        logger.error(f"Error exporting conversation: {str(e)}")
        raise

def export_json(conversation: List[Dict[str, str]], filename: str, include_metadata: bool = True) -> None:
    """Export conversation as JSON"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(conversation, f, indent=2, ensure_ascii=False)

def export_text(conversation: List[Dict[str, str]], filename: str) -> None:
    """Export conversation as plain text"""
    with open(filename, 'w', encoding='utf-8') as f:
        for message in conversation:
            role = message.get("role", "unknown").capitalize()
            content = message.get("content", "")
            
            f.write(f"{role}:\n")
            f.write(f"{content}\n\n")
            f.write("-" * 80 + "\n\n")

def export_markdown(conversation: List[Dict[str, str]], filename: str) -> None:
    """Export conversation as Markdown"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("# Conversation Export\n\n")
        
        for message in conversation:
            role = message.get("role", "unknown").capitalize()
            content = message.get("content", "")
            
            f.write(f"## {role}\n\n")
            f.write(f"{content}\n\n")
            f.write("---\n\n")

def export_html(conversation: List[Dict[str, str]], filename: str) -> None:
    """Export conversation as HTML"""
    with open(filename, 'w', encoding='utf-8') as f:
        # Write HTML header
        f.write("""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Conversation Export</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .message {
            margin-bottom: 20px;
            padding-bottom: 20px;
            border-bottom: 1px solid #eee;
        }
        .role {
            font-weight: bold;
            margin-bottom: 5px;
        }
        .user .role {
            color: #2c3e50;
        }
        .assistant .role {
            color: #3498db;
        }
        pre {
            background-color: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
        }
        code {
            font-family: monospace;
        }
    </style>
</head>
<body>
    <h1>Conversation Export</h1>
""")
        
        # Write each message
        for message in conversation:
            role = message.get("role", "unknown").lower()
            content = message.get("content", "")
            
            # Convert markdown to HTML for the content
            html_content = markdown.markdown(content, extensions=['fenced_code', 'tables'])
            
            f.write(f'    <div class="message {role}">\n')
            f.write(f'        <div class="role">{role.capitalize()}</div>\n')
            f.write(f'        <div class="content">{html_content}</div>\n')
            f.write('    </div>\n')
        
        # Close HTML document
        f.write("</body>\n</html>")

def export_csv(conversation: List[Dict[str, str]], filename: str) -> None:
    """Export conversation as CSV"""
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow(["Role", "Content"])
        
        # Write each message
        for message in conversation:
            role = message.get("role", "unknown")
            content = message.get("content", "")
            
            # Replace newlines in content to avoid breaking CSV format
            content = content.replace('\n', ' ').replace('\r', '')
            
            writer.writerow([role, content])

def export_all_formats(conversation: List[Dict[str, str]]) -> str:
    """Export conversation in all supported formats and create a ZIP file"""
    try:
        # Create a timestamp for filenames
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        base_filename = f"conversation_{timestamp}"
        
        # Export in each format
        export_files = []
        for format in EXPORT_FORMATS:
            export_path = export_conversation(conversation, format, f"{base_filename}.{format}")
            export_files.append(export_path)
            
        # Create a ZIP file containing all exports
        zip_filename = os.path.join(EXPORT_DIR, f"{base_filename}_all.zip")
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for file in export_files:
                zipf.write(file, os.path.basename(file))
                
        logger.info(f"All formats exported to ZIP: {zip_filename}")
        return zip_filename
    
    except Exception as e:
        logger.error(f"Error exporting all formats: {str(e)}")
        raise

def import_conversation(filepath: str) -> List[Dict[str, str]] | str:
    """Import a conversation from a file"""
    try:
        # Check if file exists
        if not os.path.exists(filepath):
            return f"File not found: {filepath}"
            
        # Determine file type from extension
        _, ext = os.path.splitext(filepath)
        ext = ext.lower()
        
        if ext == '.json':
            # Import JSON format
            with open(filepath, 'r', encoding='utf-8') as f:
                conversation = json.load(f)
                
            # Validate conversation format
            if not isinstance(conversation, list):
                return "Invalid conversation format: not a list"
                
            for item in conversation:
                if not isinstance(item, dict) or "role" not in item or "content" not in item:
                    return "Invalid conversation format: messages missing role or content"
                    
            return conversation
            
        elif ext in ['.txt', '.md', '.html', '.csv']:
            return f"Importing from {ext} format is not supported yet"
            
        else:
            return f"Unsupported file format: {ext}"
    
    except json.JSONDecodeError:
        return "Invalid JSON file format"
    except Exception as e:
        logger.error(f"Error importing conversation: {str(e)}")
        return f"Error importing conversation: {str(e)}"