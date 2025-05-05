"""
Offline mode functionality for The Engineer.

This module provides offline mode features including response caching,
connection status checking, and fallback behavior when API calls fail.
"""

import os
import json
import logging
import time
import socket
import requests
from typing import Dict, List, Any, Tuple, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Directory for storing cached responses
CACHE_DIR = "cache"
CACHE_FILE = os.path.join(CACHE_DIR, "response_cache.json")

# Maximum cache age in seconds (default: 7 days)
MAX_CACHE_AGE = 7 * 24 * 60 * 60

# Cache data (loaded in memory)
response_cache = {}

def initialize_cache() -> None:
    """Initialize the response cache"""
    global response_cache
    
    try:
        # Create cache directory if it doesn't exist
        os.makedirs(CACHE_DIR, exist_ok=True)
        
        # Load cache if it exists
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                response_cache = json.load(f)
                
            # Clean up expired entries
            clean_expired_cache()
            
        logger.info("Response cache initialized")
    except Exception as e:
        logger.error(f"Error initializing cache: {str(e)}")
        response_cache = {}

def save_cache() -> None:
    """Save the response cache to disk"""
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(response_cache, f, indent=2)
        logger.info("Response cache saved")
    except Exception as e:
        logger.error(f"Error saving cache: {str(e)}")

def clean_expired_cache() -> None:
    """Remove expired entries from the cache"""
    global response_cache
    
    try:
        current_time = time.time()
        expired_keys = []
        
        for key, entry in response_cache.items():
            if current_time - entry.get("timestamp", 0) > MAX_CACHE_AGE:
                expired_keys.append(key)
                
        # Remove expired entries
        for key in expired_keys:
            del response_cache[key]
            
        if expired_keys:
            logger.info(f"Removed {len(expired_keys)} expired cache entries")
            
        # Save the cleaned cache
        save_cache()
    except Exception as e:
        logger.error(f"Error cleaning cache: {str(e)}")

def cache_response(query: str, response: str, history_length: int = 0) -> None:
    """Cache a response for future use"""
    global response_cache
    
    try:
        # Create a normalized key from the query
        key = query.lower().strip()
        
        # Store the response with metadata
        response_cache[key] = {
            "response": response,
            "timestamp": time.time(),
            "history_length": history_length
        }
        
        # Save the updated cache
        save_cache()
        logger.info(f"Cached response for query: {query[:30]}...")
    except Exception as e:
        logger.error(f"Error caching response: {str(e)}")

def get_cached_response(query: str, max_age: int = MAX_CACHE_AGE) -> Optional[str]:
    """Get a cached response if available and not expired"""
    try:
        # Create a normalized key from the query
        key = query.lower().strip()
        
        # Check if we have a cached response
        if key in response_cache:
            entry = response_cache[key]
            current_time = time.time()
            
            # Check if the cache entry is still valid
            if current_time - entry.get("timestamp", 0) <= max_age:
                logger.info(f"Using cached response for query: {query[:30]}...")
                return entry.get("response")
                
        return None
    except Exception as e:
        logger.error(f"Error retrieving cached response: {str(e)}")
        return None

def clear_cache() -> bool:
    """Clear the entire response cache"""
    global response_cache
    
    try:
        response_cache = {}
        
        # Remove the cache file if it exists
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
            
        logger.info("Response cache cleared")
        return True
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        return False

def get_connection_status() -> bool:
    """Check if the application has an internet connection"""
    try:
        # Try to connect to Anthropic's API endpoint
        socket.create_connection(("api.anthropic.com", 443), timeout=5)
        return True
    except (socket.timeout, socket.error):
        # Fallback to a more general check
        try:
            requests.get("https://www.google.com", timeout=5)
            return True
        except (requests.ConnectionError, requests.Timeout):
            return False
    
    return False

def call_claude_with_fallback(message: str, conversation_history=None, api_key=None, system_prompt=None) -> Tuple[str, List[Dict[str, str]]]:
    """Call Claude with offline fallback if the API is unavailable"""
    # Check for a cached response first
    cached_response = get_cached_response(message)
    
    if cached_response:
        logger.info("Using cached response")
        
        # Create updated conversation history
        updated_history = []
        if conversation_history:
            updated_history = conversation_history.copy()
            
        # Add the user message and response to the history
        updated_history.append({"role": "user", "content": message})
        updated_history.append({"role": "assistant", "content": cached_response})
        
        return cached_response, updated_history
    
    # No cached response, generate a fallback response
    logger.info("Generating fallback response")
    
    # Basic response matching for common queries
    fallback_responses = {
        "hello": "Hello! I'm currently in offline mode, but I'll try to assist you as best I can with limited functionality.",
        "hi": "Hi there! I'm currently running in offline mode with limited capabilities.",
        "how are you": "I'm operating in offline mode currently, so I have limited capabilities. But I'm ready to help however I can.",
        "help": "I'm currently in offline mode. I can still help with basic tasks and information that doesn't require API access.",
    }
    
    # Look for matches in the fallback responses
    for key, response in fallback_responses.items():
        if key in message.lower():
            fallback = response
            break
    else:
        # Default fallback message
        fallback = """I'm currently operating in offline mode and cannot access the Claude API.

I've saved your message and will process it when the connection is restored.

In the meantime, you can:
1. Check your internet connection
2. Verify your API key is correct
3. Try a different query that might have a cached response
4. Use the /offline commands to manage offline mode"""
    
    # Create updated conversation history
    updated_history = []
    if conversation_history:
        updated_history = conversation_history.copy()
        
    # Add the user message and fallback response to the history
    updated_history.append({"role": "user", "content": message})
    updated_history.append({"role": "assistant", "content": fallback})
    
    return fallback, updated_history

def add_custom_response(keyword: str, response: str) -> bool:
    """Add a custom response to the cache for specific keywords"""
    try:
        if not keyword or not response:
            return False
            
        # Normalize the keyword
        key = keyword.lower().strip()
        
        # Add to cache directly
        cache_response(key, response)
        return True
    except Exception as e:
        logger.error(f"Error adding custom response: {str(e)}")
        return False

def get_cache_status() -> Dict[str, Any]:
    """Get the current status of the response cache"""
    try:
        cache_size = len(response_cache)
        cache_file_size = os.path.getsize(CACHE_FILE) if os.path.exists(CACHE_FILE) else 0
        
        # Calculate average age of cache entries
        total_age = 0
        current_time = time.time()
        
        for entry in response_cache.values():
            age = current_time - entry.get("timestamp", current_time)
            total_age += age
            
        avg_age = total_age / cache_size if cache_size > 0 else 0
        
        return {
            "entries": cache_size,
            "file_size_bytes": cache_file_size,
            "file_size_kb": round(cache_file_size / 1024, 2),
            "avg_age_seconds": round(avg_age, 2),
            "avg_age_days": round(avg_age / (24 * 60 * 60), 2),
            "max_age_days": round(MAX_CACHE_AGE / (24 * 60 * 60), 2)
        }
    except Exception as e:
        logger.error(f"Error getting cache status: {str(e)}")
        return {
            "error": str(e)
        }

def offline_command(command: str, *args) -> str:
    """Handle offline mode commands"""
    if command == "status":
        online = get_connection_status()
        return f"Offline mode status:\n- Connection: {'Online' if online else 'Offline'}\n- Cache entries: {len(response_cache)}"
        
    elif command == "cache_status":
        status = get_cache_status()
        if "error" in status:
            return f"Error getting cache status: {status['error']}"
            
        return f"Cache Status:\n- Entries: {status['entries']}\n- Size: {status['file_size_kb']} KB\n- Average age: {status['avg_age_days']} days\n- Maximum age: {status['max_age_days']} days"
        
    elif command == "clear_cache":
        if clear_cache():
            return "Cache cleared successfully."
        else:
            return "Error clearing cache."
            
    elif command == "add_response":
        if len(args) < 2:
            return "Usage: /offline add_response <keyword> <response>"
            
        keyword = args[0]
        response = " ".join(args[1:])
        
        if add_custom_response(keyword, response):
            return f"Custom response added for keyword: {keyword}"
        else:
            return f"Error adding custom response for keyword: {keyword}"
    
    else:
        return f"Unknown offline command: {command}\n\nAvailable commands:\n- status\n- cache_status\n- clear_cache\n- add_response <keyword> <response>"