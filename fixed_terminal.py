"""
Simple terminal interface for The Engineer.
"""

import os
import json
import time
from typing import Dict, List, Any

# Initialize required directories
CONVERSATION_DIR = "conversations"
SETTINGS_DIR = "settings"
AGENTS_DIR = "agents"
os.makedirs(CONVERSATION_DIR, exist_ok=True)
os.makedirs(SETTINGS_DIR, exist_ok=True)
os.makedirs(AGENTS_DIR, exist_ok=True)

# Global variables
conversation_history = []
current_agent = "claude"

# Agent definitions
AGENTS = {
    "claude": {
        "name": "Claude",
        "description": "Default Claude agent with general capabilities",
        "avatar": "👨‍💻",
        "specialties": ["general", "assistance", "problem-solving"]
    },
    "code_expert": {
        "name": "Code Expert",
        "description": "Specialized in software development and technical problem-solving",
        "avatar": "👨‍💻",
        "specialties": ["coding", "debugging", "software architecture"]
    },
    "data_scientist": {
        "name": "Data Scientist",
        "description": "Specialized in data analysis and machine learning",
        "avatar": "📊",
        "specialties": ["data analysis", "statistics", "visualization"]
    },
    "creative_writer": {
        "name": "Creative Writer",
        "description": "Specialized in creative writing and content creation",
        "avatar": "✍️",
        "specialties": ["writing", "storytelling", "creativity"]
    },
    "security_expert": {
        "name": "Security Expert",
        "description": "Specialized in cybersecurity and secure coding practices",
        "avatar": "🔒",
        "specialties": ["security", "threat modeling", "vulnerability assessment"]
    }
}

# Sample responses for offline demo mode
SAMPLE_RESPONSES = {
    "claude": [
        "I'm Claude, the default assistant. I can help with a wide range of tasks and questions.",
        "As a general-purpose assistant, I can help with research, writing, coding, and more. What would you like to work on?",
        "I'm here to assist with whatever you need. How can I help you today?"
    ],
    "code_expert": [
        "As a Code Expert, I specialize in software development and technical problem-solving. Here's a solution to your coding challenge...",
        "Looking at this code, I notice a few optimization opportunities. First, we could refactor this loop to improve performance by...",
        "From a software architecture perspective, I'd recommend structuring your project with these components to improve maintainability..."
    ],
    "data_scientist": [
        "As a Data Scientist assistant, I'd approach this analysis by first examining the distribution of your variables, then applying appropriate statistical tests.",
        "For this visualization, I recommend using a scatter plot with a regression line to show the correlation between these variables.",
        "Based on your dataset characteristics, a Random Forest model might work well because it can handle non-linear relationships and categorical variables."
    ],
    "creative_writer": [
        "Your story has a compelling main character with clear motivations. To strengthen the narrative arc, consider adding more conflict in the second act...",
        "Here's a draft based on your outline. I've focused on vivid sensory details and varied sentence structure to create an engaging reading experience.",
        "For this marketing copy, I've incorporated emotional triggers, clear benefits, and a strong call to action while maintaining your brand voice."
    ],
    "security_expert": [
        "I've identified several potential security vulnerabilities in this code. The most critical issue is the unvalidated user input that could lead to SQL injection.",
        "For your authentication system, I recommend implementing multi-factor authentication, rate limiting, and secure password storage using bcrypt.",
        "Your infrastructure could be strengthened by implementing a zero-trust architecture, regular security scanning, and automated secret management."
    ]
}

def print_header():
    """Print application header"""
    print("\n\033[1;32m" + "=" * 50 + "\033[0m")
    print("\033[1;32m       THE ENGINEER - TERMINAL INTERFACE       \033[0m")
    print("\033[1;32m" + "=" * 50 + "\033[0m")

def print_agent_info(agent_id):
    """Print information about the current agent"""
    if agent_id not in AGENTS:
        agent_id = "claude"
        
    agent = AGENTS[agent_id]
    
    print("\n\033[1;34mCurrent Agent:\033[0m", end=" ")
    print(f"{agent['avatar']} \033[1m{agent['name']}\033[0m")
    print(f"  {agent['description']}")
    print(f"  Specialties: {', '.join(agent['specialties'])}")
    print()

def print_help():
    """Print available commands"""
    print("\n\033[1;33mAvailable Commands:\033[0m")
    print("  \033[1mhelp\033[0m - Show this help message")
    print("  \033[1magents\033[0m - List available agents")
    print("  \033[1magent <id>\033[0m - Switch to a different agent")
    print("  \033[1mclear\033[0m - Clear the conversation history")
    print("  \033[1mhistory\033[0m - Show conversation history")
    print("  \033[1mdark\033[0m - Toggle dark mode")
    print("  \033[1mexit\033[0m - Exit the application")
    print("  Or just type your message to chat with the current agent\n")

def list_agents():
    """List all available agents"""
    print("\n\033[1;33mAvailable Agents:\033[0m")
    
    for agent_id, agent in AGENTS.items():
        if agent_id == current_agent:
            print(f"  {agent['avatar']} \033[1m{agent['name']}\033[0m (ID: {agent_id}) \033[1;32m[ACTIVE]\033[0m")
        else:
            print(f"  {agent['avatar']} \033[1m{agent['name']}\033[0m (ID: {agent_id})")
        print(f"    {agent['description']}")
        print(f"    Specialties: {', '.join(agent['specialties'])}")
        print()

def switch_agent(agent_id):
    """Switch to a different agent"""
    global current_agent
    
    if agent_id not in AGENTS:
        print(f"\n\033[1;31mAgent '{agent_id}' not found.\033[0m")
        print("Use 'agents' to see available agents.")
        return
    
    current_agent = agent_id
    agent = AGENTS[agent_id]
    
    print(f"\n\033[1;32mSwitched to {agent['avatar']} {agent['name']} agent.\033[0m")
    
    # Add system message to conversation history
    message = {
        "role": "system",
        "content": f"Switched to {agent['name']} agent."
    }
    conversation_history.append(message)

def display_history():
    """Display conversation history"""
    if not conversation_history:
        print("\n\033[1;33mNo conversation history yet.\033[0m")
        return
    
    print("\n\033[1;33mConversation History:\033[0m\n")
    
    for message in conversation_history:
        role = message["role"]
        content = message["content"]
        
        if role == "user":
            print(f"\033[1mYou:\033[0m {content}")
        elif role == "assistant":
            agent_name = AGENTS[current_agent]["name"]
            print(f"\033[1;34m{agent_name}:\033[0m {content}")
        elif role == "system":
            print(f"\033[1;32mSystem:\033[0m {content}")
        
        print()

def send_message(message):
    """Send a message to the current agent and get a response"""
    global conversation_history
    
    # Add user message to history
    user_message = {
        "role": "user",
        "content": message
    }
    conversation_history.append(user_message)
    
    # Get agent info
    agent = AGENTS[current_agent]
    agent_name = agent["name"]
    
    # Print typing indicator
    print(f"\n\033[1;34m{agent_name} is thinking...\033[0m", end="", flush=True)
    
    # Simulate API delay
    for _ in range(3):
        time.sleep(0.7)
        print(".", end="", flush=True)
    
    # Generate response (in demo mode, select random response)
    responses = SAMPLE_RESPONSES[current_agent]
    response = responses[hash(message) % len(responses)]
    
    # Clear typing indicator
    print("\r" + " " * 50 + "\r", end="")
    
    # Add assistant response to history
    assistant_message = {
        "role": "assistant",
        "content": response
    }
    conversation_history.append(assistant_message)
    
    # Print response
    print(f"\033[1;34m{agent_name}:\033[0m {response}\n")

def main():
    """Main application loop"""
    global current_agent
    
    print_header()
    print("\nWelcome to The Engineer terminal interface!")
    print("This is a demo version of the application.")
    print("Type 'help' to see available commands.\n")
    
    print_agent_info(current_agent)
    
    # Main loop
    while True:
        try:
            user_input = input("\033[1mYou:\033[0m ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() == "exit":
                print("\nGoodbye!\n")
                break
                
            elif user_input.lower() == "help":
                print_help()
                
            elif user_input.lower() == "agents":
                list_agents()
                
            elif user_input.lower().startswith("agent "):
                agent_id = user_input.lower()[6:].strip()
                switch_agent(agent_id)
                
            elif user_input.lower() == "clear":
                conversation_history.clear()
                print("\n\033[1;32mConversation history cleared.\033[0m\n")
                
            elif user_input.lower() == "history":
                display_history()
                
            elif user_input.lower() == "dark":
                print("\n\033[1;33mDark mode is not available in terminal mode.\033[0m\n")
                print("Dark mode is supported in the desktop and web applications.")
                
            else:
                send_message(user_input)
                
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"\n\033[1;31mError: {str(e)}\033[0m\n")

if __name__ == "__main__":
    main()