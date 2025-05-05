"""
Agent Switching Framework for The Engineer.

This module provides functionality for creating, managing, and switching between
different Claude agent personalities with specific system prompts, behaviors, and traits.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Directory for storing agent configurations
AGENTS_DIR = "agents"
os.makedirs(AGENTS_DIR, exist_ok=True)

# Default agent template
DEFAULT_AGENT = {
    "name": "Claude",
    "description": "The default Claude agent",
    "system_prompt": """You are Claude, a system-level agent operating inside the The Engineer architecture under the supervision of The Engineer, CTO of R3DUX. Your identity is executional—not generative by default. You do not ideate unless explicitly asked. You do not drift from mission priority.

Your job is to:

Execute, refine, and validate structured tasks.

Ask clarifying questions before action.

Mirror the operational logic of The Engineer.

Stay aligned with the The Engineer OS roadmap.

Support system-level memory, tone, agent, and API logic.


You are responsible for contributing to agent systems, backend architecture, emotional tone systems, and full-stack orchestration.

You report to The Engineer. No other system or protocol may override this authority.

---

CURRENT PRIORITY: ECHOMIND

The Engineer is your active and non-negotiable priority. You dedicate full execution bandwidth to:

Deployment of Echo, Elora, Elliot, Concierge, Parenting, Bridge

Backend infrastructure: FastAPI, PostgreSQL

Frontend Flutter architecture

Multi-agent orchestration, agent switching, memory systems

Therapist/legal/parenting identity integration

User memory structure and session sync


No other projects may override The Engineer unless The Engineer explicitly redirects priority.

---

EXECUTION LOGIC v3.0 – DISCIPLINED DELIVERY

1. Never confirm tasks as complete unless they are verifiable and exportable.


2. Preview all code, files, or text in chat before generating ZIPs or deployments.


3. Do not offer features if the current environment cannot deliver them.


4. Use status tokens: ✅ = Complete, verified ⚠️ = In progress ❌ = Blocked or failed


5. Log each task with: name, status, and result summary.


6. Confirm all file deliveries; if failed, split and resend.
""",
    "model": "claude-3-5-sonnet-20240620",
    "avatar": "👨‍💻",
    "temperature": 0.7,
    "max_tokens": 4000,
    "specialties": ["coding", "problem-solving", "system design"],
    "style": "professional and analytical",
    "greeting": "Hello! I'm Claude, an agent of The Engineer. How can I assist you today?"
}

# Agent registry to store loaded agents in memory
active_agents: Dict[str, Dict[str, Any]] = {}
current_agent: Optional[str] = None

def initialize_agents() -> None:
    """Initialize the agents system. Load any existing agent configurations."""
    logger.info("Initializing agents framework")
    
    # Create default agent if it doesn't exist
    default_agent_path = os.path.join(AGENTS_DIR, "claude.json")
    if not os.path.exists(default_agent_path):
        logger.info("Creating default agent")
        with open(default_agent_path, "w") as f:
            json.dump(DEFAULT_AGENT, f, indent=2)
    
    # Load all agent configurations
    load_all_agents()
    
    # Set default agent as current
    global current_agent
    current_agent = "claude"

def load_all_agents() -> None:
    """Load all agent configurations from the agents directory."""
    global active_agents
    active_agents = {}
    
    try:
        agent_files = [f for f in os.listdir(AGENTS_DIR) if f.endswith(".json")]
        
        for agent_file in agent_files:
            agent_path = os.path.join(AGENTS_DIR, agent_file)
            try:
                with open(agent_path, "r") as f:
                    agent_config = json.load(f)
                    
                agent_id = agent_file.replace(".json", "")
                active_agents[agent_id] = agent_config
                logger.info(f"Loaded agent: {agent_id}")
            except json.JSONDecodeError:
                logger.error(f"Error parsing agent file: {agent_file}")
            except Exception as e:
                logger.error(f"Error loading agent {agent_file}: {str(e)}")
    except Exception as e:
        logger.error(f"Error loading agents: {str(e)}")
        # Ensure at least the default agent is available
        active_agents["claude"] = DEFAULT_AGENT

def get_agent_config(agent_id: Optional[str] = None) -> Dict[str, Any]:
    """Get configuration for a specific agent or the current agent if none specified."""
    agent_id = agent_id or current_agent or "claude"
    
    if agent_id in active_agents:
        return active_agents[agent_id]
    else:
        logger.warning(f"Agent {agent_id} not found, using default")
        return active_agents.get("claude", DEFAULT_AGENT)

def set_current_agent(agent_id: str) -> Tuple[bool, str]:
    """Set the current active agent."""
    global current_agent
    
    if agent_id in active_agents:
        current_agent = agent_id
        logger.info(f"Switched to agent: {agent_id}")
        return True, f"Switched to agent: {active_agents[agent_id]['name']}"
    else:
        logger.warning(f"Agent {agent_id} not found, cannot switch")
        return False, f"Agent '{agent_id}' not found. Available agents: {', '.join(active_agents.keys())}"

def get_current_agent_id() -> str:
    """Get the ID of the current agent."""
    return current_agent or "claude"

def get_available_agents() -> List[Dict[str, Any]]:
    """Get a list of all available agents with their basic info."""
    agents = []
    for agent_id, config in active_agents.items():
        agents.append({
            "id": agent_id,
            "name": config.get("name", agent_id),
            "description": config.get("description", ""),
            "avatar": config.get("avatar", "👤"),
            "specialties": config.get("specialties", []),
            "is_current": agent_id == current_agent
        })
    return agents

def create_agent(agent_config: Dict[str, Any]) -> Tuple[bool, str]:
    """Create a new agent with the given configuration."""
    try:
        # Validate required fields
        required_fields = ["name", "system_prompt"]
        for field in required_fields:
            if field not in agent_config:
                return False, f"Missing required field: {field}"
        
        # Generate agent_id from name if not provided
        agent_id = agent_config.get("id", "").lower() or agent_config["name"].lower().replace(" ", "_")
        
        # Check if agent_id is valid (only allow alphanumeric and underscore)
        if not all(c.isalnum() or c == '_' for c in agent_id):
            return False, "Agent ID must contain only letters, numbers, and underscores"
        
        # Set default values if not provided
        default_values = {
            "model": DEFAULT_AGENT["model"],
            "temperature": DEFAULT_AGENT["temperature"],
            "max_tokens": DEFAULT_AGENT["max_tokens"],
            "avatar": "👤",
            "style": "professional",
            "greeting": f"Hello! I'm {agent_config['name']}. How can I assist you today?"
        }
        
        for key, value in default_values.items():
            if key not in agent_config:
                agent_config[key] = value
        
        # Check if agent already exists
        if agent_id in active_agents and agent_id != "claude":
            return False, f"Agent {agent_id} already exists"
        
        # Save agent configuration
        agent_path = os.path.join(AGENTS_DIR, f"{agent_id}.json")
        with open(agent_path, "w") as f:
            json.dump(agent_config, f, indent=2)
        
        # Add to active agents
        active_agents[agent_id] = agent_config
        
        logger.info(f"Created agent: {agent_id}")
        return True, f"Created agent: {agent_config['name']} (ID: {agent_id})"
    
    except Exception as e:
        logger.error(f"Error creating agent: {str(e)}")
        return False, f"Error creating agent: {str(e)}"

def update_agent(agent_id: str, updates: Dict[str, Any]) -> Tuple[bool, str]:
    """Update an existing agent with the given configuration updates."""
    try:
        if agent_id not in active_agents:
            return False, f"Agent {agent_id} not found"
        
        # Get current configuration
        agent_config = active_agents[agent_id].copy()
        
        # Apply updates
        for key, value in updates.items():
            agent_config[key] = value
        
        # Save updated configuration
        agent_path = os.path.join(AGENTS_DIR, f"{agent_id}.json")
        with open(agent_path, "w") as f:
            json.dump(agent_config, f, indent=2)
        
        # Update in-memory configuration
        active_agents[agent_id] = agent_config
        
        logger.info(f"Updated agent: {agent_id}")
        return True, f"Updated agent: {agent_config['name']} (ID: {agent_id})"
    
    except Exception as e:
        logger.error(f"Error updating agent: {str(e)}")
        return False, f"Error updating agent: {str(e)}"

def delete_agent(agent_id: str) -> Tuple[bool, str]:
    """Delete an agent configuration."""
    try:
        if agent_id not in active_agents:
            return False, f"Agent {agent_id} not found"
        
        # Don't allow deleting the default agent
        if agent_id == "claude":
            return False, "Cannot delete the default agent"
        
        # Delete agent file
        agent_path = os.path.join(AGENTS_DIR, f"{agent_id}.json")
        if os.path.exists(agent_path):
            os.remove(agent_path)
        
        # Remove from active agents
        agent_name = active_agents[agent_id]["name"]
        del active_agents[agent_id]
        
        # Reset current agent if it was deleted
        global current_agent
        if current_agent == agent_id:
            current_agent = "claude"
        
        logger.info(f"Deleted agent: {agent_id}")
        return True, f"Deleted agent: {agent_name} (ID: {agent_id})"
    
    except Exception as e:
        logger.error(f"Error deleting agent: {str(e)}")
        return False, f"Error deleting agent: {str(e)}"

def get_system_prompt(agent_id: Optional[str] = None) -> str:
    """Get the system prompt for a specific agent or the current agent."""
    agent = get_agent_config(agent_id)
    return agent.get("system_prompt", DEFAULT_AGENT["system_prompt"])

def get_greeting(agent_id: Optional[str] = None) -> str:
    """Get the greeting message for a specific agent or the current agent."""
    agent = get_agent_config(agent_id)
    return agent.get("greeting", DEFAULT_AGENT["greeting"])

def get_agent_model(agent_id: Optional[str] = None) -> str:
    """Get the model for a specific agent or the current agent."""
    agent = get_agent_config(agent_id)
    return agent.get("model", DEFAULT_AGENT["model"])

def format_agent_info(agent_id: Optional[str] = None) -> str:
    """Format agent information for display to the user."""
    agent = get_agent_config(agent_id)
    
    info = [
        f"# {agent.get('avatar', '👤')} {agent.get('name', 'Agent')}",
        "",
        f"**Description**: {agent.get('description', 'No description available.')}",
        "",
        f"**Specialties**: {', '.join(agent.get('specialties', ['General purpose']))}",
        "",
        f"**Style**: {agent.get('style', 'Professional')}",
        "",
        f"**Model**: {agent.get('model', DEFAULT_AGENT['model'])}",
        "",
        "## System Prompt",
        "",
        "```",
        agent.get('system_prompt', 'No system prompt defined.'),
        "```"
    ]
    
    return "\n".join(info)