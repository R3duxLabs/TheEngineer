"""
Settings management module for The Engineer.

This module provides functionality for storing and retrieving user settings
with persistence between sessions.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Settings directory
SETTINGS_DIR = "settings"
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")

# Default settings
DEFAULT_SETTINGS = {
    "theme": "light",
    "font_size": "medium",
    "save_history": True,
    "max_history": 100,
    "code_style": "default",
    "domain": None,
    "current_agent": "claude",
    "offline_mode": {
        "enabled": False,
        "cache_responses": True,
        "max_cache_size": 1000
    }
}

# Global settings variable
settings = {}

def initialize_settings() -> Dict[str, Any]:
    """Initialize settings from file or create defaults"""
    global settings
    
    try:
        # Create settings directory if it doesn't exist
        os.makedirs(SETTINGS_DIR, exist_ok=True)
        
        # Load settings if file exists
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                loaded_settings = json.load(f)
                
            # Merge with defaults to ensure all required settings exist
            settings = DEFAULT_SETTINGS.copy()
            settings.update(loaded_settings)
        else:
            # Use defaults and create settings file
            settings = DEFAULT_SETTINGS.copy()
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=2)
                
        logger.info("Settings initialized successfully")
        return settings
    except Exception as e:
        logger.error(f"Error initializing settings: {str(e)}")
        return DEFAULT_SETTINGS.copy()

def save_settings() -> bool:
    """Save current settings to file"""
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        logger.info("Settings saved successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving settings: {str(e)}")
        return False

def get_setting(key: str, default: Any = None) -> Any:
    """Get a setting value by key"""
    # Get from global settings, with fallback to default parameter
    return settings.get(key, default)

def update_setting(key: str, value: Any) -> bool:
    """Update a setting value and save settings"""
    try:
        # Update in memory
        settings[key] = value
        
        # Save to disk
        save_settings()
        logger.info(f"Updated setting: {key} = {value}")
        return True
    except Exception as e:
        logger.error(f"Error updating setting {key}: {str(e)}")
        return False

def reset_to_defaults() -> bool:
    """Reset all settings to default values"""
    try:
        global settings
        settings = DEFAULT_SETTINGS.copy()
        save_settings()
        logger.info("Settings reset to defaults")
        return True
    except Exception as e:
        logger.error(f"Error resetting settings: {str(e)}")
        return False

def format_settings_display() -> str:
    """Format settings for display to the user"""
    output = "Current Settings:\n\n"
    
    # Format each setting category
    if "theme" in settings:
        output += f"Theme: {settings['theme']}\n"
    
    if "font_size" in settings:
        output += f"Font Size: {settings['font_size']}\n"
    
    if "domain" in settings and settings["domain"]:
        output += f"Active Domain: {settings['domain']}\n"
    else:
        output += "Active Domain: default\n"
        
    if "current_agent" in settings:
        output += f"Current Agent: {settings['current_agent']}\n"
    
    if "save_history" in settings:
        output += f"Save Conversation History: {'Yes' if settings['save_history'] else 'No'}\n"
    
    if "max_history" in settings:
        output += f"Maximum History Entries: {settings['max_history']}\n"
    
    if "code_style" in settings:
        output += f"Code Highlighting Style: {settings['code_style']}\n"
    
    # Format offline mode settings
    offline = settings.get("offline_mode", {})
    output += "\nOffline Mode Settings:\n"
    output += f"  Enabled: {'Yes' if offline.get('enabled', False) else 'No'}\n"
    output += f"  Cache Responses: {'Yes' if offline.get('cache_responses', True) else 'No'}\n"
    output += f"  Max Cache Size: {offline.get('max_cache_size', 1000)} entries\n"
    
    return output