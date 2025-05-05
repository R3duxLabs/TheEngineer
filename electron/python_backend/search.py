"""
Search functionality for The Engineer application.
Enables searching through conversation history and files.
"""
import os
import json
import re
from datetime import datetime
import logging

# Set up logging
logger = logging.getLogger(__name__)

def search_conversations(query, conversations_dir="conversations"):
    """
    Search through all saved conversations for a query string.
    Returns a list of matches with conversation filename and matching messages.
    """
    results = []
    
    # Ensure the conversations directory exists
    if not os.path.exists(conversations_dir):
        logger.warning(f"Conversations directory {conversations_dir} does not exist")
        return results
    
    # Get all conversation files
    conversation_files = [f for f in os.listdir(conversations_dir) if f.endswith('.json')]
    
    if not conversation_files:
        logger.info("No conversation files found to search")
        return results
    
    # Create case-insensitive pattern for more flexible matching
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    
    # Search through each conversation file
    for filename in conversation_files:
        filepath = os.path.join(conversations_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                conversation = json.load(f)
            
            # Search through messages
            file_matches = []
            for i, message in enumerate(conversation):
                if 'content' in message and pattern.search(message['content']):
                    # Extract a snippet around the match for context
                    content = message['content']
                    match_pos = content.lower().find(query.lower())
                    start = max(0, match_pos - 50)
                    end = min(len(content), match_pos + len(query) + 50)
                    
                    # Add ellipsis if we're not at the beginning/end
                    prefix = "..." if start > 0 else ""
                    suffix = "..." if end < len(content) else ""
                    
                    snippet = f"{prefix}{content[start:end]}{suffix}"
                    
                    file_matches.append({
                        'message_index': i,
                        'role': message.get('role', 'unknown'),
                        'snippet': snippet,
                        'timestamp': message.get('timestamp', None)
                    })
            
            if file_matches:
                # Parse timestamp from filename if present (conversation_YYYYMMDD_HHMMSS.json)
                timestamp = None
                timestamp_match = re.search(r'conversation_(\d{8}_\d{6})\.json', filename)
                if timestamp_match:
                    try:
                        date_str = timestamp_match.group(1)
                        timestamp = datetime.strptime(date_str, "%Y%m%d_%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        pass
                
                results.append({
                    'filename': filename,
                    'matches': file_matches,
                    'match_count': len(file_matches),
                    'timestamp': timestamp
                })
                
        except Exception as e:
            logger.error(f"Error searching conversation file {filename}: {str(e)}")
    
    # Sort results by number of matches (most matches first)
    results.sort(key=lambda x: x['match_count'], reverse=True)
    
    return results

def format_search_results(results, max_matches=3):
    """Format search results for display to the user"""
    if not results:
        return "No matches found."
    
    output = f"Found matches in {len(results)} conversation(s):\n\n"
    
    for result in results:
        filename = result['filename']
        timestamp = f" ({result['timestamp']})" if result['timestamp'] else ""
        output += f"📄 {filename}{timestamp} - {result['match_count']} matches\n"
        
        # Show the first few matches as examples
        for i, match in enumerate(result['matches'][:max_matches]):
            role = match['role'].capitalize()
            output += f"  {role}: {match['snippet']}\n"
        
        # Indicate if there were more matches
        if len(result['matches']) > max_matches:
            output += f"  ... and {len(result['matches']) - max_matches} more matches\n"
        
        output += "\n"
    
    return output

def search_current_conversation(query, conversation_history):
    """Search the current in-memory conversation for a query string"""
    if not conversation_history:
        return "No conversation history to search."
    
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    matches = []
    
    for i, message in enumerate(conversation_history):
        if 'content' in message and pattern.search(message['content']):
            # Extract a snippet around the match for context
            content = message['content']
            match_pos = content.lower().find(query.lower())
            start = max(0, match_pos - 50)
            end = min(len(content), match_pos + len(query) + 50)
            
            # Add ellipsis if we're not at the beginning/end
            prefix = "..." if start > 0 else ""
            suffix = "..." if end < len(content) else ""
            
            snippet = f"{prefix}{content[start:end]}{suffix}"
            
            matches.append({
                'message_index': i,
                'role': message.get('role', 'unknown'),
                'snippet': snippet
            })
    
    if not matches:
        return "No matches found in current conversation."
    
    output = f"Found {len(matches)} matches in current conversation:\n\n"
    for match in matches:
        role = match['role'].capitalize()
        output += f"{role}: {match['snippet']}\n\n"
    
    return output