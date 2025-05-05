import json
import os

def list_saved_conversations():
    """List all saved conversations"""
    conversations_dir = "conversations"
    if not os.path.exists(conversations_dir):
        os.makedirs(conversations_dir, exist_ok=True)
    conversations = [f for f in os.listdir(conversations_dir) if f.endswith(".json")]
    return conversations

def load_conversation(filename):
    """Load a conversation from a file"""
    try:
        conversations_dir = "conversations"
        filepath = os.path.join(conversations_dir, filename)
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception as e:
        return f"Error loading conversation: {str(e)}"