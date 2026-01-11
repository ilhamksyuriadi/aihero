import os
import json
import secrets
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from pydantic_ai.messages import ModelMessagesTypeAdapter


# Use environment variable or default to 'logs'
LOG_DIR = Path(os.getenv('LOGS_DIRECTORY', 'logs'))
LOG_DIR.mkdir(exist_ok=True)


class ConversationLogger:
    def __init__(self, log_dir: Optional[str] = None):
        """
        Initialize logger with optional custom directory.
        
        Args:
            log_dir: Custom log directory (default: from env or 'logs')
        """
        if log_dir:
            self.log_dir = Path(log_dir)
        else:
            self.log_dir = LOG_DIR
        
        self.log_dir.mkdir(exist_ok=True)
    
    def _serializer(self, obj):
        """Custom JSON serializer for datetime objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    def create_log_entry(
        self, 
        agent, 
        messages, 
        query: str, 
        response: str,
        source: str = "user"
    ) -> Dict[str, Any]:
        """
        Create a log entry from agent interaction.
        
        Args:
            agent: The agent instance
            messages: Agent messages
            query: User query
            response: Agent response
            source: Source of the query
        
        Returns:
            Dictionary log entry
        """
        # Get tools used by the agent
        tools = []
        if hasattr(agent, 'toolsets'):
            for ts in agent.toolsets:
                tools.extend(ts.tools.keys())
        
        # Convert messages to dict if they're model messages
        dict_messages = None
        try:
            dict_messages = ModelMessagesTypeAdapter.dump_python(messages)
        except:
            dict_messages = str(messages)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "agent_name": getattr(agent, 'name', 'unknown_agent'),
            "system_prompt": getattr(agent, '_instructions', ''),
            "model": getattr(getattr(agent, 'model', None), 'model_name', 'unknown'),
            "tools": tools,
            "query": query,
            "response": response,
            "messages": dict_messages,
            "source": source
        }
    
    def log_interaction(
        self,
        agent,
        messages,
        query: str,
        response: str,
        source: str = "user"
    ) -> Path:
        """
        Log an interaction to a JSON file.
        
        Args:
            agent: The agent instance
            messages: Agent messages
            query: User query
            response: Agent response
            source: Source of the query
        
        Returns:
            Path to the log file
        """
        # Create log entry
        entry = self.create_log_entry(agent, messages, query, response, source)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        rand_hex = secrets.token_hex(3)
        agent_name = entry.get('agent_name', 'agent').replace(' ', '_')
        
        filename = f"{agent_name}_{timestamp}_{rand_hex}.json"
        filepath = self.log_dir / filename
        
        # Write to file
        with filepath.open("w", encoding="utf-8") as f_out:
            json.dump(entry, f_out, indent=2, default=self._serializer)
        
        print(f"📝 Log saved to: {filepath}")
        return filepath
    
    def log_simple(self, query: str, response: str, agent_name: str = "agent") -> Path:
        """
        Simple logging without full agent context.
        
        Args:
            query: User query
            response: Agent response
            agent_name: Name of the agent
        
        Returns:
            Path to the log file
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_name": agent_name,
            "query": query,
            "response": response
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"simple_{agent_name}_{timestamp}.json"
        filepath = self.log_dir / filename
        
        with filepath.open("w", encoding="utf-8") as f_out:
            json.dump(entry, f_out, indent=2)
        
        print(f"📝 Simple log saved to: {filepath}")
        return filepath
    
    def get_recent_logs(self, limit: int = 10) -> list:
        """
        Get recent log entries.
        
        Args:
            limit: Maximum number of logs to return
        
        Returns:
            List of log entries
        """
        try:
            log_files = sorted(self.log_dir.glob("*.json"), 
                             key=lambda x: x.stat().st_mtime, 
                             reverse=True)
            
            logs = []
            for filepath in log_files[:limit]:
                try:
                    with filepath.open("r", encoding="utf-8") as f_in:
                        logs.append(json.load(f_in))
                except json.JSONDecodeError:
                    continue
            
            return logs
        except FileNotFoundError:
            return []


# Create default logger instance for convenience
default_logger = ConversationLogger()


# Convenience functions
def log_to_file(agent, messages, query: str, response: str, source: str = "user"):
    """Convenience function to log interaction."""
    return default_logger.log_interaction(agent, messages, query, response, source)


def log_simple_interaction(query: str, response: str, agent_name: str = "agent"):
    """Convenience function for simple logging."""
    return default_logger.log_simple(query, response, agent_name)