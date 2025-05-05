"""
Settings management for The Engineer application.
Handles persistent storage and retrieval of user preferences and settings.
"""

import os
import json
import logging
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

# Settings directory and file
SETTINGS_DIR = "settings"
SETTINGS_FILE = "user_settings.json"
SETTINGS_PATH = os.path.join(SETTINGS_DIR, SETTINGS_FILE)

# Default settings
DEFAULT_SETTINGS = {
    "domain": None,               # Default domain (None = default system prompt)
    "model": "claude-3-5-sonnet-20240620",  # Default model to use
    "max_tokens": 4000,           # Default max tokens for responses
    "chat_history_size": 100,     # Maximum number of messages to keep in history
    "theme": "light",             # UI theme (light/dark)
    "show_thinking": True,        # Show "thinking" indicators
    "timestamp_format": "%Y-%m-%d %H:%M:%S",  # Format for displayed timestamps
    "last_modified": datetime.now().isoformat(),
    "created_at": datetime.now().isoformat()
}

# Current settings (loaded from file or defaults)
current_settings = {}

def initialize_settings():
    """Initialize settings directory and file if they don't exist"""
    global current_settings
    
    # Create settings directory if it doesn't exist
    if not os.path.exists(SETTINGS_DIR):
        logger.info(f"Creating settings directory: {SETTINGS_DIR}")
        os.makedirs(SETTINGS_DIR, exist_ok=True)
    
    # Load settings from file or create with defaults
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                stored_settings = json.load(f)
                
            # Merge with defaults to ensure all keys exist (in case new settings were added)
            current_settings = DEFAULT_SETTINGS.copy()
            current_settings.update(stored_settings)
            logger.info("Settings loaded from file")
        except Exception as e:
            logger.error(f"Error loading settings: {str(e)}")
            current_settings = DEFAULT_SETTINGS.copy()
    else:
        # No settings file exists, use defaults
        current_settings = DEFAULT_SETTINGS.copy()
        save_settings()
        logger.info("Created default settings file")
    
    return current_settings

def get_setting(key, default=None):
    """Get a setting value by key, with optional default"""
    if not current_settings:
        initialize_settings()
    
    return current_settings.get(key, default)

def update_setting(key, value):
    """Update a single setting by key"""
    if not current_settings:
        initialize_settings()
    
    if key in current_settings:
        current_settings[key] = value
        current_settings["last_modified"] = datetime.now().isoformat()
        save_settings()
        return True
    else:
        logger.warning(f"Attempted to update unknown setting: {key}")
        return False

def update_settings(settings_dict):
    """Update multiple settings at once"""
    if not current_settings:
        initialize_settings()
    
    # Only update known settings
    valid_updates = {k: v for k, v in settings_dict.items() if k in current_settings}
    
    if valid_updates:
        current_settings.update(valid_updates)
        current_settings["last_modified"] = datetime.now().isoformat()
        save_settings()
        
    if len(valid_updates) != len(settings_dict):
        logger.warning(f"Some settings were not recognized and were ignored")
    
    return len(valid_updates) > 0

def save_settings():
    """Save current settings to file"""
    try:
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(current_settings, f, indent=2)
        logger.info("Settings saved to file")
        return True
    except Exception as e:
        logger.error(f"Error saving settings: {str(e)}")
        return False

def reset_to_defaults():
    """Reset all settings to default values"""
    global current_settings
    current_settings = DEFAULT_SETTINGS.copy()
    current_settings["last_modified"] = datetime.now().isoformat()
    save_settings()
    logger.info("Settings reset to defaults")
    return True

def get_all_settings():
    """Get all current settings"""
    if not current_settings:
        initialize_settings()
    
    return current_settings

def format_settings_display():
    """Format current settings for display to the user"""
    settings = get_all_settings()
    
    output = "Current Settings:\n\n"
    
    # Skip internal fields like created_at and last_modified
    skip_fields = ['created_at', 'last_modified']
    
    for key, value in settings.items():
        if key not in skip_fields:
            if key == 'domain' and value is None:
                output += f"{key}: default\n"
            else:
                output += f"{key}: {value}\n"
    
    return output