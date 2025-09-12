"""Settings and configuration management for the agent system.

This module provides centralized configuration management with support for
a structured JSON configuration file.
"""

import json
from typing import Any, Dict, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LangfuseConfig:
    """Configuration for Langfuse observability."""
    public_key: str = ""
    secret_key: str = ""
    host: str = "https://cloud.langfuse.com"


@dataclass
class LLMConfig:
    """Configuration for LLM providers."""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    model_name: str = "gpt-4"
    model_temperature: float = 0.0


@dataclass
class Neo4jConfig:
    """Configuration for Neo4j database."""
    uri: str = "bolt://localhost:7687"
    username: str = "neo4j"
    password: str = "password"


@dataclass
class AgentConfig:
    """Configuration for agent behavior."""
    max_retries: int = 3
    checkpointer_type: str = "memory"
    tracer_type: str = "console"


@dataclass
class DevelopmentConfig:
    """Configuration for development and debugging."""
    debug: bool = False
    log_level: str = "INFO"


class Settings:
    """Centralized settings management for the agent system.
    
    This class provides a single point of configuration management,
    loading settings from a JSON file.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize settings with optional configuration file.
        
        Args:
            config_file: Optional path to a JSON configuration file.
                        If not provided, will look for `config.json` in the current directory.
        """
        self.config_file = config_file or "config.json"
        
        config = self._load_config()

        # Initialize configuration sections from JSON file, with dataclass defaults
        self.langfuse = LangfuseConfig(**config.get('langfuse', {}))
        self.llm = LLMConfig(**config.get('llm', {}))
        self.neo4j = Neo4jConfig(**config.get('neo4j', {}))
        self.agent = AgentConfig(**config.get('agent', {}))
        self.dev = DevelopmentConfig(**config.get('dev', {}))
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file if it exists.
        
        Returns an empty dictionary if the file doesn't exist or is invalid.
        """
        config_path = Path(self.config_file)
        if config_path.exists():
            with open(config_path, 'r') as f:
                try:
                    content = f.read()
                    if not content:
                        return {}
                    return json.loads(content)
                except json.JSONDecodeError:
                    # Handle empty or invalid JSON file
                    return {}
        return {}
    
    @property
    def model_name(self) -> str:
        """Get the configured model name."""
        return self.llm.model_name
    
    @property
    def max_retries(self) -> int:
        """Get the maximum number of retries."""
        return self.agent.max_retries
    
    @property
    def checkpointer_type(self) -> str:
        """Get the checkpointer type."""
        return self.agent.checkpointer_type
    
    @property
    def tracer_type(self) -> str:
        """Get the tracer type."""
        return self.agent.tracer_type
    
    @property
    def debug(self) -> bool:
        """Get debug mode status."""
        return self.dev.debug
    
    def get_graph_store_config(self) -> Dict[str, Any]:
        """Get graph store configuration.
        
        Returns:
            Dictionary with graph store configuration.
        """
        return {
            "kind": "memory",  # Default to memory, can be overridden
            "neo4j": {
                "uri": self.neo4j.uri,
                "username": self.neo4j.username,
                "password": self.neo4j.password,
            }
        }
    
    def get_context_manager_config(self) -> Dict[str, Any]:
        """Get context manager configuration.
        
        Returns:
            Dictionary with context manager configuration.
        """
        return {
            "kind": "simple",  # Default to simple, progressive can be enabled
            "max_retries": self.max_retries,
            "debug": self.debug,
        }
    
    def get_tool_registry_config(self) -> Dict[str, Any]:
        """Get tool registry configuration.
        
        Returns:
            Dictionary with tool registry configuration.
        """
        return {
            "kind": "standard",
            "llm_config": {
                "model_name": self.model_name,
                "temperature": self.llm.model_temperature,
                "openai_api_key": self.llm.openai_api_key,
                "anthropic_api_key": self.llm.anthropic_api_key,
            }
        }
    
    def get_tracer_config(self) -> Dict[str, Any]:
        """Get tracer configuration.
        
        Returns:
            Dictionary with tracer configuration.
        """
        return {
            "kind": self.tracer_type,
            "langfuse": {
                "public_key": self.langfuse.public_key,
                "secret_key": self.langfuse.secret_key,
                "host": self.langfuse.host,
            },
            "debug": self.debug,
        }
    
    def get_agent_config(self) -> Dict[str, Any]:
        """Get agent configuration.
        
        Returns:
            Dictionary with agent configuration.
        """
        return {
            "graph_store": self.get_graph_store_config(),
            "context_manager": self.get_context_manager_config(),
            "tool_registry": self.get_tool_registry_config(),
            "tracer": self.get_tracer_config(),
            "checkpointer": {
                "checkpointer_type": self.checkpointer_type,
            }
        }
    
    def validate(self) -> None:
        """Validate configuration settings.
        
        Raises:
            ValueError: If required configuration is missing or invalid.
        """
        # Validate tracer type
        valid_tracers = ["console", "noop", "langfuse"]
        if self.tracer_type not in valid_tracers:
            raise ValueError(f"Invalid tracer type: {self.tracer_type}. Must be one of {valid_tracers}")
        
        # Validate checkpointer type
        valid_checkpointers = ["memory", "file", "redis"]
        if self.checkpointer_type not in valid_checkpointers:
            raise ValueError(f"Invalid checkpointer type: {self.checkpointer_type}. Must be one of {valid_checkpointers}")
        
        # Validate model temperature
        if not 0.0 <= self.llm.model_temperature <= 2.0:
            raise ValueError(f"Model temperature must be between 0.0 and 2.0, got {self.llm.model_temperature}")
        
        # Validate max retries
        if self.max_retries < 0:
            raise ValueError(f"Max retries must be non-negative, got {self.max_retries}")
        
        # Validate Langfuse config if using langfuse tracer
        if self.tracer_type == "langfuse":
            if not self.langfuse.public_key or not self.langfuse.secret_key:
                raise ValueError("Langfuse public_key and secret_key are required when using langfuse tracer")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary for serialization.
        
        Returns:
            Dictionary representation of all settings.
        """
        return {
            "langfuse": {
                "public_key": self.langfuse.public_key,
                "secret_key": "***" if self.langfuse.secret_key else "",  # Redact secret
                "host": self.langfuse.host,
            },
            "llm": {
                "model_name": self.llm.model_name,
                "model_temperature": self.llm.model_temperature,
                "openai_api_key": "***" if self.llm.openai_api_key else "",  # Redact secret
                "anthropic_api_key": "***" if self.llm.anthropic_api_key else "",  # Redact secret
            },
            "neo4j": {
                "uri": self.neo4j.uri,
                "username": self.neo4j.username,
                "password": "***" if self.neo4j.password else "",  # Redact secret
            },
            "agent": {
                "max_retries": self.agent.max_retries,
                "checkpointer_type": self.agent.checkpointer_type,
                "tracer_type": self.agent.tracer_type,
            },
            "dev": {
                "debug": self.dev.debug,
                "log_level": self.dev.log_level,
            }
        }


# Global settings instance
settings = Settings()
