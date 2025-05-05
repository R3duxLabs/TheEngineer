"""
Search functionality for conversations in The Engineer.

This module provides functions to search through current and saved conversations.
"""

import os
import json
import logging
import re
from typing import Dict, List, Any, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def search_current_conversation(query: str, conversation_history: List[Dict[str, str]]) -> str:
    """Search the current in-memory conversation for a query string"""
    if not query or not conversation_history:
        return "No results found."
        
    results = []
    query_lower = query.lower()
    
    for i, message in enumerate(conversation_history):
        if query_lower in message.get("content", "").lower():
            # Extract a snippet of text around the match
            content = message.get("content", "")
            role = message.get("role", "unknown").capitalize()
            
            # Find all occurrences of the query (case insensitive)
            matches = []
            for match in re.finditer(re.escape(query_lower), content.lower()):
                start_pos = max(0, match.start() - 50)
                end_pos = min(len(content), match.end() + 50)
                
                # Get the surrounding text
                if start_pos > 0:
                    snippet = "..." + content[start_pos:end_pos] + "..."
                else:
                    snippet = content[start_pos:end_pos] + "..."
                    
                # Highlight the matched text
                snippet = re.sub(
                    re.escape(query), 
                    lambda m: f"**{m.group(0)}**", 
                    snippet, 
                    flags=re.IGNORECASE
                )
                
                matches.append(snippet)
            
            # Add this message to results
            results.append({
                "index": i,
                "role": role,
                "matches": matches
            })
    
    # Format the results
    if results:
        output = f"Found {len(results)} messages containing '{query}':\n\n"
        for result in results:
            output += f"Message #{result['index'] + 1} from {result['role']}:\n"
            for i, match in enumerate(result['matches']):
                output += f"  Match {i+1}: {match}\n"
            output += "\n"
        return output
    else:
        return f"No results found for '{query}'."

def search_conversations(query: str, conversations_dir: str) -> List[Tuple[str, List[Dict[str, Any]]]]:
    """Search through all saved conversations for a query string"""
    if not query or not os.path.exists(conversations_dir):
        return []
        
    results = []
    query_lower = query.lower()
    
    try:
        # Get all conversation files
        conversation_files = [f for f in os.listdir(conversations_dir) if f.endswith('.json')]
        
        for filename in conversation_files:
            filepath = os.path.join(conversations_dir, filename)
            
            try:
                with open(filepath, 'r') as f:
                    conversation = json.load(f)
                    
                # Search through this conversation
                file_results = []
                
                for i, message in enumerate(conversation):
                    if query_lower in message.get("content", "").lower():
                        # Extract a snippet of text around the match
                        content = message.get("content", "")
                        role = message.get("role", "unknown").capitalize()
                        
                        # Find all occurrences of the query (case insensitive)
                        matches = []
                        for match in re.finditer(re.escape(query_lower), content.lower()):
                            start_pos = max(0, match.start() - 50)
                            end_pos = min(len(content), match.end() + 50)
                            
                            # Get the surrounding text
                            if start_pos > 0:
                                snippet = "..." + content[start_pos:end_pos] + "..."
                            else:
                                snippet = content[start_pos:end_pos] + "..."
                                
                            # Highlight the matched text
                            snippet = re.sub(
                                re.escape(query), 
                                lambda m: f"**{m.group(0)}**", 
                                snippet, 
                                flags=re.IGNORECASE
                            )
                            
                            matches.append(snippet)
                        
                        # Add this message to results
                        file_results.append({
                            "index": i,
                            "role": role,
                            "matches": matches
                        })
                
                # If there were matches in this file, add to overall results
                if file_results:
                    results.append((filename, file_results))
                    
            except json.JSONDecodeError:
                logger.error(f"Error parsing conversation file: {filename}")
            except Exception as e:
                logger.error(f"Error processing file {filename}: {str(e)}")
                
        return results
        
    except Exception as e:
        logger.error(f"Error searching conversations: {str(e)}")
        return []

def format_search_results(results: List[Tuple[str, List[Dict[str, Any]]]]) -> str:
    """Format search results for display"""
    if not results:
        return "No results found in saved conversations."
        
    output = f"Found matches in {len(results)} conversation files:\n\n"
    
    for filename, file_results in results:
        output += f"File: {filename} ({len(file_results)} matches)\n"
        
        for result in file_results[:3]:  # Limit to 3 matches per file
            output += f"  Message #{result['index'] + 1} from {result['role']}:\n"
            for i, match in enumerate(result['matches'][:2]):  # Limit to 2 snippets per message
                output += f"    Match {i+1}: {match}\n"
        
        if len(file_results) > 3:
            output += f"  ... and {len(file_results) - 3} more matches in this file\n"
            
        output += "\n"
    
    return output