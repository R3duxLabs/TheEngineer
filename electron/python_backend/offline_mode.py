"""
Offline mode functionality for The Engineer application.
Provides fallback capabilities when API access is not available.
"""

import os
import json
import logging
import datetime
import sqlite3
import hashlib
from typing import List, Dict, Any, Optional, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cache directory and database
CACHE_DIR = "cache"
CACHE_DB = os.path.join(CACHE_DIR, "response_cache.db")
OFFLINE_RESPONSES_FILE = os.path.join(CACHE_DIR, "offline_responses.json")

# Default offline responses for common message patterns
DEFAULT_OFFLINE_RESPONSES = {
    "hello": "Hello! I'm currently operating in offline mode, but I can still help with basic tasks and cached responses.",
    "help": "I'm in offline mode, but I can still help with file operations, search, and other local functions. API-dependent features like code analysis with Claude are limited to cached responses.",
    "analyze": "I'm in offline mode and can't perform real-time code analysis with Claude. Try using the built-in code analyzer or check cached analyses.",
    "error": "I'm currently in offline mode due to API connection issues. I can still assist with local operations like file management, search, and other non-API dependent tasks.",
    "default": "I'm operating in offline mode currently. I can help with local operations, but tasks requiring the Claude API are limited to cached responses."
}

def initialize_cache():
    """Initialize the cache directory and database"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR, exist_ok=True)
    
    # Initialize the cache database
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS response_cache (
        request_hash TEXT PRIMARY KEY,
        request TEXT,
        response TEXT,
        timestamp TEXT,
        ttl INTEGER
    )
    ''')
    
    # Create index on request_hash
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_request_hash ON response_cache (request_hash)')
    
    conn.commit()
    conn.close()
    
    # Initialize offline responses file if it doesn't exist
    if not os.path.exists(OFFLINE_RESPONSES_FILE):
        with open(OFFLINE_RESPONSES_FILE, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_OFFLINE_RESPONSES, f, indent=2)
    
    logger.info("Cache system initialized")

def get_request_hash(request: Dict[str, Any]) -> str:
    """Generate a hash for a request"""
    # Extract the essential parts of the request to create a consistent hash
    key_parts = []
    
    # For API requests, use the model and messages
    if 'model' in request and 'messages' in request:
        key_parts.append(request['model'])
        for message in request['messages']:
            if isinstance(message, dict) and 'content' in message and 'role' in message:
                key_parts.append(f"{message['role']}:{message['content']}")
    
    # For other requests, use the request as a string
    else:
        key_parts.append(str(request))
    
    # Create a hash from the combined key parts
    key = '|'.join(key_parts)
    return hashlib.md5(key.encode('utf-8')).hexdigest()

def cache_response(request: Dict[str, Any], response: Dict[str, Any], ttl: int = 24*60*60) -> None:
    """
    Cache a response for future use
    
    Args:
        request: The request dictionary
        response: The response dictionary
        ttl: Time to live in seconds (default: 24 hours)
    """
    # Generate a hash for the request
    request_hash = get_request_hash(request)
    
    # Connect to the database
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    
    # Store the request and response
    timestamp = datetime.datetime.now().isoformat()
    cursor.execute(
        'INSERT OR REPLACE INTO response_cache (request_hash, request, response, timestamp, ttl) VALUES (?, ?, ?, ?, ?)',
        (request_hash, json.dumps(request), json.dumps(response), timestamp, ttl)
    )
    
    conn.commit()
    conn.close()
    
    logger.info(f"Cached response for request hash {request_hash[:8]}...")

def get_cached_response(request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Get a cached response for a request
    
    Args:
        request: The request dictionary
        
    Returns:
        The cached response or None if not found or expired
    """
    # Generate a hash for the request
    request_hash = get_request_hash(request)
    
    # Connect to the database
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    
    # Get the cached response
    cursor.execute('SELECT response, timestamp, ttl FROM response_cache WHERE request_hash = ?', (request_hash,))
    result = cursor.fetchone()
    
    conn.close()
    
    if not result:
        return None
    
    response_json, timestamp_str, ttl = result
    
    # Check if the cache entry has expired
    timestamp = datetime.datetime.fromisoformat(timestamp_str)
    age = (datetime.datetime.now() - timestamp).total_seconds()
    
    if age > ttl:
        logger.info(f"Cache entry expired for request hash {request_hash[:8]}...")
        return None
    
    logger.info(f"Retrieved cached response for request hash {request_hash[:8]}...")
    return json.loads(response_json)

def clear_expired_cache_entries():
    """Clear expired cache entries"""
    # Connect to the database
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    
    # Get all cache entries
    cursor.execute('SELECT request_hash, timestamp, ttl FROM response_cache')
    entries = cursor.fetchall()
    
    # Check which entries have expired
    now = datetime.datetime.now()
    expired_hashes = []
    
    for request_hash, timestamp_str, ttl in entries:
        timestamp = datetime.datetime.fromisoformat(timestamp_str)
        age = (now - timestamp).total_seconds()
        
        if age > ttl:
            expired_hashes.append(request_hash)
    
    # Delete expired entries
    if expired_hashes:
        cursor.executemany('DELETE FROM response_cache WHERE request_hash = ?', [(h,) for h in expired_hashes])
        conn.commit()
        logger.info(f"Cleared {len(expired_hashes)} expired cache entries")
    
    conn.close()

def get_offline_response(message: str) -> Tuple[str, List[Dict[str, str]]]:
    """
    Get an appropriate offline response for a message
    
    Args:
        message: The user message
        
    Returns:
        A tuple containing (response text, updated conversation history)
    """
    # Load custom offline responses
    offline_responses = DEFAULT_OFFLINE_RESPONSES.copy()
    if os.path.exists(OFFLINE_RESPONSES_FILE):
        try:
            with open(OFFLINE_RESPONSES_FILE, 'r', encoding='utf-8') as f:
                custom_responses = json.load(f)
                offline_responses.update(custom_responses)
        except Exception as e:
            logger.error(f"Error loading offline responses: {str(e)}")
    
    # Find the best matching response based on keywords
    message_lower = message.lower()
    
    for keyword, response in offline_responses.items():
        if keyword.lower() in message_lower:
            logger.info(f"Using offline response for keyword: {keyword}")
            
            # Create conversation history entries
            conversation = [
                {"role": "user", "content": message},
                {"role": "assistant", "content": response}
            ]
            
            return response, conversation
    
    # If no specific match, use the default response
    logger.info("Using default offline response")
    conversation = [
        {"role": "user", "content": message},
        {"role": "assistant", "content": offline_responses["default"]}
    ]
    
    return offline_responses["default"], conversation

def add_custom_offline_response(keyword: str, response: str) -> bool:
    """
    Add a custom offline response for a keyword
    
    Args:
        keyword: The keyword to match in messages
        response: The response to provide
        
    Returns:
        True if successful, False otherwise
    """
    # Load existing responses
    offline_responses = DEFAULT_OFFLINE_RESPONSES.copy()
    if os.path.exists(OFFLINE_RESPONSES_FILE):
        try:
            with open(OFFLINE_RESPONSES_FILE, 'r', encoding='utf-8') as f:
                custom_responses = json.load(f)
                offline_responses.update(custom_responses)
        except Exception as e:
            logger.error(f"Error loading offline responses: {str(e)}")
    
    # Add or update the response
    offline_responses[keyword] = response
    
    # Save back to file
    try:
        with open(OFFLINE_RESPONSES_FILE, 'w', encoding='utf-8') as f:
            json.dump(offline_responses, f, indent=2)
        logger.info(f"Added custom offline response for keyword: {keyword}")
        return True
    except Exception as e:
        logger.error(f"Error saving offline responses: {str(e)}")
        return False

def get_connection_status() -> bool:
    """
    Check if the application can connect to the Anthropic API
    
    Returns:
        True if connected, False otherwise
    """
    import requests
    
    try:
        # Try a simple HEAD request to anthropic.com
        response = requests.head("https://api.anthropic.com", timeout=5)
        return response.status_code < 400
    except:
        # Any exception means we're offline
        return False

def call_claude_with_fallback(message: str, conversation_history=None, api_key=None, system_prompt=None):
    """
    Call Claude with offline fallback if the API is unavailable
    
    Args:
        message: The user message
        conversation_history: Optional conversation history
        api_key: API key for Claude
        system_prompt: System prompt to use
        
    Returns:
        A tuple containing (response text, updated conversation history)
    """
    # Imports here to avoid circular imports
    import requests
    
    # Check if we're online
    online = get_connection_status()
    
    # If offline or no API key, use offline mode
    if not online or not api_key:
        logger.warning("Using offline mode for Claude API call")
        
        # First check if we have a cached response
        request = {
            "model": "claude-3-5-sonnet-20240620",
            "messages": conversation_history + [{"role": "user", "content": message}] if conversation_history else [{"role": "user", "content": message}],
            "system": system_prompt
        }
        
        cached_response = get_cached_response(request)
        
        if cached_response:
            # Extract text from cached response
            try:
                response_text = cached_response.get("content", [{"text": ""}])[0].get("text", "")
                
                # Update conversation history
                messages = conversation_history.copy() if conversation_history else []
                messages.append({"role": "user", "content": message})
                messages.append({"role": "assistant", "content": response_text})
                
                return f"[Cached] {response_text}", messages
            except Exception as e:
                logger.error(f"Error processing cached response: {str(e)}")
        
        # If no cached response, use offline responses
        return get_offline_response(message)
    
    # Online and have API key, try to call Claude
    try:
        # Prepare the API call
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Prepare messages
        messages = []
        if conversation_history:
            messages = conversation_history.copy()
        
        # Add new user message
        messages.append({"role": "user", "content": message})
        
        # Prepare request data
        data = {
            "model": "claude-3-5-sonnet-20240620",
            "max_tokens": 4000,
            "system": system_prompt,
            "messages": messages
        }
        
        # Make the API call
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=15
        )
        
        # Check for successful response
        if response.status_code == 200:
            response_data = response.json()
            assistant_message = response_data["content"][0]["text"]
            
            # Cache the response for future offline use
            cache_response(data, response_data)
            
            # Update conversation history
            messages.append({"role": "assistant", "content": assistant_message})
            
            return assistant_message, messages
        else:
            # API error, try offline mode
            logger.error(f"API Error ({response.status_code}), falling back to offline mode")
            return get_offline_response(message)
            
    except Exception as e:
        # Exception during API call, use offline mode
        logger.error(f"Exception during API call: {str(e)}")
        return get_offline_response(message)

def offline_command(command, *args):
    """Handle special offline commands"""
    if command == "cache_status":
        # Get cache status
        try:
            conn = sqlite3.connect(CACHE_DB)
            cursor = conn.cursor()
            
            # Count total entries
            cursor.execute('SELECT COUNT(*) FROM response_cache')
            total_entries = cursor.fetchone()[0]
            
            # Count expired entries
            now = datetime.datetime.now()
            expired_count = 0
            
            cursor.execute('SELECT timestamp, ttl FROM response_cache')
            for timestamp_str, ttl in cursor.fetchall():
                timestamp = datetime.datetime.fromisoformat(timestamp_str)
                age = (now - timestamp).total_seconds()
                if age > ttl:
                    expired_count += 1
            
            conn.close()
            
            # Calculate cache size
            cache_size = os.path.getsize(CACHE_DB) if os.path.exists(CACHE_DB) else 0
            cache_size_mb = cache_size / (1024 * 1024)
            
            return f"Cache status:\n- Total entries: {total_entries}\n- Expired entries: {expired_count}\n- Cache size: {cache_size_mb:.2f} MB"
        
        except Exception as e:
            return f"Error getting cache status: {str(e)}"
    
    elif command == "clear_cache":
        # Clear all or expired cache entries
        try:
            if args and args[0] == "expired":
                # Clear only expired entries
                clear_expired_cache_entries()
                return "Cleared expired cache entries"
            else:
                # Clear all cache entries
                conn = sqlite3.connect(CACHE_DB)
                cursor = conn.cursor()
                cursor.execute('DELETE FROM response_cache')
                conn.commit()
                conn.close()
                return "Cleared all cache entries"
        except Exception as e:
            return f"Error clearing cache: {str(e)}"
    
    elif command == "add_response":
        # Add a custom offline response
        if len(args) >= 2:
            keyword = args[0]
            response = args[1]
            
            if add_custom_offline_response(keyword, response):
                return f"Added custom offline response for keyword: {keyword}"
            else:
                return f"Error adding custom offline response for keyword: {keyword}"
        else:
            return "Usage: offline add_response <keyword> <response>"
    
    # Unknown command
    return f"Unknown offline command: {command}"