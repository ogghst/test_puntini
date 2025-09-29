"""Settings and configuration management for the agent system.

This module provides centralized configuration management with support for
a structured JSON configuration file.
"""

import json
from typing import Any, Dict, Optional, List
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LangfuseConfig:
    """Configuration for Langfuse observability."""
    public_key: str = ""
    secret_key: str = ""
    host: str = "https://cloud.langfuse.com"
    debug: bool = False
    tracing_enabled: bool = True
    sample_rate: float = 1.0
    environment: str = "default"
    release: str = ""
    session_id: str = ""
    user_id: str = ""


@dataclass
class ModelInfo:
    """Model capability information."""
    family: str = ""
    vision: bool = False
    function_calling: bool = False
    json_output: bool = False
    structured_output: bool = False


@dataclass
class LLMProviderConfig:
    """Configuration for a single LLM provider."""
    name: str = ""
    type: str = ""  # "openai", "anthropic", "ollama", etc.
    api_key: str = ""
    model_name: str = ""
    temperature: float = 0.0
    max_tokens: int = 2000
    enabled: bool = True
    base_url: str = ""  # Custom API endpoint
    model_info: Optional[ModelInfo] = None
    
    def __post_init__(self):
        """Initialize model_info if not provided."""
        if self.model_info is None:
            self.model_info = ModelInfo()


@dataclass
class LLMConfig:
    """Configuration for LLM providers using a list-based approach."""
    default_llm: str = "openai-gpt4"
    providers: List[LLMProviderConfig] = None
    
    def __post_init__(self):
        """Initialize LLM provider configurations after dataclass creation."""
        if self.providers is None:
            # Default providers if none specified
            self.providers = [
                LLMProviderConfig(
                    name="openai-gpt4",
                    type="openai",
                    api_key="",
                    model_name="gpt-4o-mini",
                    temperature=0.1,
                    max_tokens=2000,
                    enabled=False
                ),
                LLMProviderConfig(
                    name="anthropic-sonnet",
                    type="anthropic",
                    api_key="",
                    model_name="claude-3-5-sonnet-latest",
                    temperature=0.0,
                    max_tokens=2000,
                    enabled=False
                )
            ]


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
class LoggingConfig:
    """Configuration for logging system."""
    log_level: str = "DEBUG"
    console_logging: bool = False
    max_bytes: int = 10485760  # 10MB
    backup_count: int = 5
    log_file: str = "backend.log"
    logs_path: str = "logs"


@dataclass
class ServerConfig:
    """Configuration for FastAPI server settings."""
    host: str = "127.0.0.1"
    port: int = 8009
    reload: bool = False
    workers: int = 1
    access_log: bool = True
    log_level: str = "info"
    root_path: str = ""
    openapi_url: str = "/openapi.json"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"


@dataclass
class DatabaseConfig:
    """Configuration for database settings."""
    type: str = "sqlite"
    location: str = "../../database/puntini.db"
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    pool_pre_ping: bool = True


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
        
        # Initialize LLM config with list-based providers
        llm_config = config.get('llm', {})
        self.llm = LLMConfig(**llm_config)
        
        # Override providers list if specified in JSON
        if 'providers' in llm_config:
            self.llm.providers = []
            for provider_config in llm_config['providers']:
                # Handle model_info separately if present
                model_info = None
                if 'model_info' in provider_config:
                    model_info = ModelInfo(**provider_config.pop('model_info'))
                
                # Create provider config
                provider = LLMProviderConfig(**provider_config)
                if model_info:
                    provider.model_info = model_info
                
                self.llm.providers.append(provider)
        
        self.neo4j = Neo4jConfig(**config.get('neo4j', {}))
        self.agent = AgentConfig(**config.get('agent', {}))
        self.database = DatabaseConfig(**config.get('database', {}))
        self.logging = LoggingConfig(**config.get('logging', {}))
        self.server = ServerConfig(**config.get('server', {}))
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
        default_llm = self.get_default_llm_config()
        return default_llm.model_name if default_llm else ""
    
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
    
    @property
    def server_host(self) -> str:
        """Get server host."""
        return self.server.host
    
    @property
    def server_port(self) -> int:
        """Get server port."""
        return self.server.port
    
    @property
    def server_reload(self) -> bool:
        """Get server reload setting."""
        return self.server.reload
    
    @property
    def server_workers(self) -> int:
        """Get server workers count."""
        return self.server.workers
    
    def get_llm_config(self, name: str) -> Optional[LLMProviderConfig]:
        """Get LLM configuration by name.
        
        Args:
            name: The name of the LLM provider.
            
        Returns:
            LLMProviderConfig if found, None otherwise.
        """
        for provider in self.llm.providers:
            if provider.name == name:
                return provider
        return None
    
    def get_available_llms(self) -> List[str]:
        """Get list of available (enabled) LLM providers.
        
        Returns:
            List of available LLM provider names.
        """
        available = []
        for provider in self.llm.providers:
            if provider.enabled:
                available.append(provider.name)
        return available
    
    def get_default_llm_config(self) -> Optional[LLMProviderConfig]:
        """Get the default LLM configuration.
        
        Returns:
            LLMProviderConfig for the default LLM, or None if not available.
        """
        default_config = self.get_llm_config(self.llm.default_llm)
        if default_config and default_config.enabled:
            return default_config
        
        # Fallback to first available LLM
        available = self.get_available_llms()
        if available:
            return self.get_llm_config(available[0])
        
        return None
    
    def get_llms_by_type(self, provider_type: str) -> List[LLMProviderConfig]:
        """Get all LLM configurations of a specific type.
        
        Args:
            provider_type: The type of provider (e.g., "openai", "anthropic").
            
        Returns:
            List of LLMProviderConfig instances matching the type.
        """
        return [provider for provider in self.llm.providers if provider.type == provider_type]
    
    def add_llm_provider(self, provider_config: LLMProviderConfig) -> None:
        """Add a new LLM provider configuration.
        
        Args:
            provider_config: The LLM provider configuration to add.
        """
        # Check if provider with same name already exists
        existing = self.get_llm_config(provider_config.name)
        if existing:
            raise ValueError(f"LLM provider with name '{provider_config.name}' already exists")
        
        self.llm.providers.append(provider_config)
    
    def remove_llm_provider(self, name: str) -> bool:
        """Remove an LLM provider configuration.
        
        Args:
            name: The name of the LLM provider to remove.
            
        Returns:
            True if provider was removed, False if not found.
        """
        for i, provider in enumerate(self.llm.providers):
            if provider.name == name:
                del self.llm.providers[i]
                return True
        return False
    
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
        default_llm = self.get_default_llm_config()
        if not default_llm:
            return {
                "kind": "standard",
                "llm_config": {}
            }
        
        return {
            "kind": "standard",
            "llm_config": {
                "model_name": default_llm.model_name,
                "temperature": default_llm.temperature,
                "api_key": default_llm.api_key,
                "base_url": default_llm.base_url,
                "provider_type": default_llm.type,
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
                "debug": self.langfuse.debug,
                "tracing_enabled": self.langfuse.tracing_enabled,
                "sample_rate": self.langfuse.sample_rate,
                "environment": self.langfuse.environment,
                "release": self.langfuse.release,
                "session_id": self.langfuse.session_id,
                "user_id": self.langfuse.user_id,
            },
            "debug": self.debug,
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration.
        
        Returns:
            Dictionary with logging configuration.
        """
        return {
            "log_level": self.logging.log_level,
            "console_logging": self.logging.console_logging,
            "max_bytes": self.logging.max_bytes,
            "backup_count": self.logging.backup_count,
            "log_file": self.logging.log_file,
            "logs_path": self.logging.logs_path,
        }
    
    def get_server_config(self) -> Dict[str, Any]:
        """Get server configuration.
        
        Returns:
            Dictionary with server configuration.
        """
        return {
            "host": self.server.host,
            "port": self.server.port,
            "reload": self.server.reload,
            "workers": self.server.workers,
            "access_log": self.server.access_log,
            "log_level": self.server.log_level,
            "root_path": self.server.root_path,
            "openapi_url": self.server.openapi_url,
            "docs_url": self.server.docs_url,
            "redoc_url": self.server.redoc_url,
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
            "logging": self.get_logging_config(),
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
        
        # Validate model temperature for all providers
        for provider in self.llm.providers:
            if not 0.0 <= provider.temperature <= 2.0:
                raise ValueError(f"Model temperature must be between 0.0 and 2.0, got {provider.temperature} for provider {provider.name}")
        
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
                "debug": self.langfuse.debug,
                "tracing_enabled": self.langfuse.tracing_enabled,
                "sample_rate": self.langfuse.sample_rate,
                "environment": self.langfuse.environment,
                "release": self.langfuse.release,
                "session_id": self.langfuse.session_id,
                "user_id": self.langfuse.user_id,
            },
            "llm": {
                "default_llm": self.llm.default_llm,
                "providers": [
                    {
                        "name": provider.name,
                        "type": provider.type,
                        "model_name": provider.model_name,
                        "temperature": provider.temperature,
                        "max_tokens": provider.max_tokens,
                        "enabled": provider.enabled,
                        "base_url": provider.base_url,
                        "api_key": "***" if provider.api_key else "",  # Redact secret
                        "model_info": {
                            "family": provider.model_info.family,
                            "vision": provider.model_info.vision,
                            "function_calling": provider.model_info.function_calling,
                            "json_output": provider.model_info.json_output,
                            "structured_output": provider.model_info.structured_output,
                        } if provider.model_info else {}
                    }
                    for provider in self.llm.providers
                ]
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
            "logging": {
                "log_level": self.logging.log_level,
                "console_logging": self.logging.console_logging,
                "max_bytes": self.logging.max_bytes,
                "backup_count": self.logging.backup_count,
                "log_file": self.logging.log_file,
                "logs_path": self.logging.logs_path,
            },
            "server": {
                "host": self.server.host,
                "port": self.server.port,
                "reload": self.server.reload,
                "workers": self.server.workers,
                "access_log": self.server.access_log,
                "log_level": self.server.log_level,
                "root_path": self.server.root_path,
                "openapi_url": self.server.openapi_url,
                "docs_url": self.server.docs_url,
                "redoc_url": self.server.redoc_url,
            },
            "dev": {
                "debug": self.dev.debug,
                "log_level": self.dev.log_level,
            }
        }


# Global settings instance
settings = Settings()
