"""
Export and import functionality for The Engineer application.
Provides tools to export conversations in different formats and import from files.
"""

import os
import json
import csv
import logging
import zipfile
import tempfile
import datetime
from bs4 import BeautifulSoup
import markdown

# Set up logging
logger = logging.getLogger(__name__)

# Export formats
EXPORT_FORMATS = ['json', 'txt', 'md', 'html', 'csv']

def export_conversation(conversation, format='json', filename=None, include_metadata=True):
    """
    Export a conversation in the specified format
    
    Args:
        conversation: List of conversation messages
        format: Export format (json, txt, md, html, csv)
        filename: Output filename (optional)
        include_metadata: Whether to include timestamps and other metadata
        
    Returns:
        Path to the exported file
    """
    if not conversation:
        return "No conversation to export"
    
    # Create export directory if it doesn't exist
    export_dir = "exports"
    if not os.path.exists(export_dir):
        os.makedirs(export_dir, exist_ok=True)
    
    # Generate filename if not provided
    if not filename:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_export_{timestamp}.{format}"
    
    # Ensure filename has correct extension
    if not filename.endswith(f".{format}"):
        filename = f"{filename}.{format}"
    
    filepath = os.path.join(export_dir, filename)
    
    try:
        if format == 'json':
            return export_json(conversation, filepath, include_metadata)
        elif format == 'txt':
            return export_txt(conversation, filepath, include_metadata)
        elif format == 'md':
            return export_md(conversation, filepath, include_metadata)
        elif format == 'html':
            return export_html(conversation, filepath, include_metadata)
        elif format == 'csv':
            return export_csv(conversation, filepath, include_metadata)
        else:
            logger.error(f"Unsupported export format: {format}")
            return f"Error: Unsupported export format: {format}"
    except Exception as e:
        logger.error(f"Error exporting conversation: {str(e)}")
        return f"Error exporting conversation: {str(e)}"

def export_json(conversation, filepath, include_metadata=True):
    """Export conversation in JSON format"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            if include_metadata:
                # Add export metadata
                export_data = {
                    "metadata": {
                        "exported_at": datetime.datetime.now().isoformat(),
                        "format": "json",
                        "message_count": len(conversation)
                    },
                    "messages": conversation
                }
                json.dump(export_data, f, indent=2)
            else:
                # Just save the raw conversation
                json.dump(conversation, f, indent=2)
        
        logger.info(f"Conversation exported to {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Error exporting to JSON: {str(e)}")
        raise

def export_txt(conversation, filepath, include_metadata=True):
    """Export conversation in plain text format"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            if include_metadata:
                f.write(f"Conversation Export (Plain Text)\n")
                f.write(f"Exported: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Messages: {len(conversation)}\n")
                f.write("-" * 80 + "\n\n")
            
            for i, message in enumerate(conversation, 1):
                role = message.get("role", "unknown").capitalize()
                content = message.get("content", "")
                
                f.write(f"{role}:\n")
                f.write(f"{content}\n\n")
                
                if i < len(conversation):
                    f.write("-" * 40 + "\n\n")
        
        logger.info(f"Conversation exported to {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Error exporting to text: {str(e)}")
        raise

def export_md(conversation, filepath, include_metadata=True):
    """Export conversation in Markdown format"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            if include_metadata:
                f.write(f"# Conversation Export (Markdown)\n\n")
                f.write(f"- **Exported:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"- **Messages:** {len(conversation)}\n\n")
                f.write("---\n\n")
            
            for message in conversation:
                role = message.get("role", "unknown").capitalize()
                content = message.get("content", "")
                
                f.write(f"## {role}\n\n")
                f.write(f"{content}\n\n")
                f.write("---\n\n")
        
        logger.info(f"Conversation exported to {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Error exporting to Markdown: {str(e)}")
        raise

def export_html(conversation, filepath, include_metadata=True):
    """Export conversation in HTML format"""
    try:
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Engineer - Conversation Export</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        .metadata {{
            background-color: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .message {{
            margin-bottom: 20px;
            padding: 15px;
            border-radius: 5px;
        }}
        .user {{
            background-color: #e6f7ff;
            border-left: 3px solid #1890ff;
        }}
        .assistant {{
            background-color: #f0f7ff;
            border-left: 3px solid #4a6fa5;
        }}
        .role {{
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .content {{
            white-space: pre-wrap;
        }}
        pre {{
            background-color: #f1f1f1;
            padding: 10px;
            border-radius: 3px;
            overflow-x: auto;
        }}
        code {{
            font-family: monospace;
            background-color: #f1f1f1;
            padding: 2px 4px;
            border-radius: 3px;
        }}
    </style>
</head>
<body>
    <h1>The Engineer - Conversation Export</h1>
"""
        
        if include_metadata:
            html_content += f"""
    <div class="metadata">
        <p><strong>Exported:</strong> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Messages:</strong> {len(conversation)}</p>
    </div>
"""
        
        for message in conversation:
            role = message.get("role", "unknown").lower()
            content = message.get("content", "")
            
            # Convert Markdown to HTML if content contains markdown
            if "```" in content or "*" in content or "#" in content:
                content_html = markdown.markdown(content)
            else:
                # Escape HTML special characters and convert newlines to <br>
                content_html = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                content_html = content_html.replace("\n", "<br>")
            
            html_content += f"""
    <div class="message {role}">
        <div class="role">{role.capitalize()}</div>
        <div class="content">{content_html}</div>
    </div>
"""
        
        html_content += """
</body>
</html>
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Conversation exported to {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Error exporting to HTML: {str(e)}")
        raise

def export_csv(conversation, filepath, include_metadata=True):
    """Export conversation in CSV format"""
    try:
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # Write headers
            writer.writerow(['Role', 'Content', 'Timestamp'])
            
            for message in conversation:
                role = message.get("role", "unknown")
                content = message.get("content", "")
                timestamp = message.get("timestamp", "")
                
                writer.writerow([role, content, timestamp])
        
        logger.info(f"Conversation exported to {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Error exporting to CSV: {str(e)}")
        raise

def export_all_formats(conversation, base_filename=None, include_metadata=True):
    """
    Export conversation in all supported formats
    
    Returns:
        Path to a zip file containing all exports
    """
    if not conversation:
        return "No conversation to export"
    
    # Create temporary directory for exports
    with tempfile.TemporaryDirectory() as temp_dir:
        export_files = []
        
        # Export in each format
        for format in EXPORT_FORMATS:
            try:
                if base_filename:
                    filename = f"{base_filename}.{format}"
                else:
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"conversation_export_{timestamp}.{format}"
                
                # Export to temp directory
                temp_path = os.path.join(temp_dir, filename)
                
                if format == 'json':
                    export_json(conversation, temp_path, include_metadata)
                elif format == 'txt':
                    export_txt(conversation, temp_path, include_metadata)
                elif format == 'md':
                    export_md(conversation, temp_path, include_metadata)
                elif format == 'html':
                    export_html(conversation, temp_path, include_metadata)
                elif format == 'csv':
                    export_csv(conversation, temp_path, include_metadata)
                
                export_files.append(temp_path)
            except Exception as e:
                logger.error(f"Error exporting to {format}: {str(e)}")
        
        # Create export directory if it doesn't exist
        export_dir = "exports"
        if not os.path.exists(export_dir):
            os.makedirs(export_dir, exist_ok=True)
        
        # Create zip file with all exports
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"conversation_export_{timestamp}.zip"
        zip_path = os.path.join(export_dir, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file in export_files:
                zipf.write(file, os.path.basename(file))
        
        logger.info(f"All formats exported to {zip_path}")
        return zip_path

def import_conversation(filepath):
    """
    Import a conversation from a file
    
    Args:
        filepath: Path to the file to import
        
    Returns:
        Imported conversation or error message
    """
    if not os.path.exists(filepath):
        return f"Error: File not found: {filepath}"
    
    file_ext = os.path.splitext(filepath)[1].lower()
    
    try:
        if file_ext == '.json':
            return import_json(filepath)
        elif file_ext == '.zip':
            return import_zip(filepath)
        else:
            return f"Error: Unsupported import format: {file_ext}"
    except Exception as e:
        logger.error(f"Error importing conversation: {str(e)}")
        return f"Error importing conversation: {str(e)}"

def import_json(filepath):
    """Import conversation from JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check if this is our export format (with metadata)
        if isinstance(data, dict) and 'messages' in data:
            conversation = data['messages']
        # Or just a plain list of messages
        elif isinstance(data, list):
            conversation = data
        else:
            return "Error: Invalid JSON format for conversation"
        
        logger.info(f"Conversation imported from {filepath}")
        return conversation
    except json.JSONDecodeError:
        return "Error: Invalid JSON file"
    except Exception as e:
        logger.error(f"Error importing from JSON: {str(e)}")
        raise

def import_zip(filepath):
    """Import conversation from ZIP file (containing a JSON file)"""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract ZIP file
            with zipfile.ZipFile(filepath, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # Look for JSON files
            json_files = [f for f in os.listdir(temp_dir) if f.endswith('.json')]
            
            if not json_files:
                return "Error: No JSON files found in the ZIP archive"
            
            # Import the first JSON file found
            return import_json(os.path.join(temp_dir, json_files[0]))
    except zipfile.BadZipFile:
        return "Error: Invalid ZIP file"
    except Exception as e:
        logger.error(f"Error importing from ZIP: {str(e)}")
        raise