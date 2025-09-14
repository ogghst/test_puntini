"""LLM Factory for creating and managing LangChain chat models.

This module provides a singleton factory class for creating and managing
different language models based on configuration settings.
"""

from typing import Dict, Optional, Any, List
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain.chat_models import init_chat_model
from langchain_ollama import ChatOllama
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_deepseek import ChatDeepSeek
from ..settings import Settings, LLMProviderConfig


class LLMFactory:
    """Singleton factory for creating and managing LangChain chat models.
    
    This factory provides a centralized way to create and manage different
    language models based on configuration settings. It supports OpenAI,
    Anthropic Claude, and other LangChain-compatible models.
    
    Example:
        >>> factory = LLMFactory()
        >>> llm = factory.get_llm("openai")
        >>> response = llm.invoke("Hello, world!")
    """
    
    _instance: Optional['LLMFactory'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'LLMFactory':
        """Create or return the singleton instance.
        
        Returns:
            The singleton LLMFactory instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the LLM factory with settings."""
        if not self._initialized:
            self.settings = Settings()
            self._models: Dict[str, BaseChatModel] = {}
            self._initialized = True
    
    def get_llm(self, name: Optional[str] = None) -> BaseChatModel:
        """Get a language model by name.
        
        Args:
            name: The name of the LLM provider. If None, returns the default LLM.
            
        Returns:
            A configured LangChain chat model.
            
        Raises:
            ValueError: If the specified LLM is not available or configured.
            RuntimeError: If no LLMs are available.
            
        Examples:
            >>> factory = LLMFactory()
            >>> # Get default LLM
            >>> llm = factory.get_llm()
            >>> # Get specific LLM
            >>> openai_llm = factory.get_llm("openai")
            >>> claude_llm = factory.get_llm("claude")
        """
        if name is None:
            name = self.settings.llm.default_llm
        
        # Return cached model if available
        if name in self._models:
            return self._models[name]
        
        # Get LLM configuration
        llm_config = self.settings.get_llm_config(name)
        if not llm_config:
            raise ValueError(f"LLM provider '{name}' not found in configuration")
        
        if not llm_config.enabled:
            raise ValueError(f"LLM provider '{name}' is disabled")
        
        if not llm_config.api_key:
            raise ValueError(f"API key not configured for LLM provider '{name}'")
        
        # Create the model based on provider type
        try:
            model = self._create_model(llm_config)
            self._models[name] = model
            return model
        except Exception as e:
            raise RuntimeError(f"Failed to create LLM '{name}': {str(e)}") from e
    
    def get_default_llm(self) -> BaseChatModel:
        """Get the default language model.
        
        Returns:
            The default configured LangChain chat model.
            
        Raises:
            RuntimeError: If no default LLM is available.
        """
        try:
            return self.get_llm()
        except (ValueError, RuntimeError):
            # Try to get any available LLM as fallback
            available_llms = self.settings.get_available_llms()
            if available_llms:
                return self.get_llm(available_llms[0])
            raise RuntimeError("No LLMs are available. Please check your configuration.")
    
    def list_available_llms(self) -> List[str]:
        """List all available LLM providers.
        
        Returns:
            List of available LLM provider names.
        """
        return self.settings.get_available_llms()
    
    def get_llm_info(self, name: Optional[str] = None) -> Dict[str, Any]:
        """Get information about an LLM provider.
        
        Args:
            name: The name of the LLM provider. If None, returns info for default LLM.
            
        Returns:
            Dictionary containing LLM provider information.
        """
        if name is None:
            name = self.settings.llm.default_llm
        
        llm_config = self.settings.get_llm_config(name)
        if not llm_config:
            return {"error": f"LLM provider '{name}' not found"}
        
        return {
            "name": llm_config.name,
            "type": llm_config.type,
            "model_name": llm_config.model_name,
            "temperature": llm_config.temperature,
            "max_tokens": llm_config.max_tokens,
            "enabled": llm_config.enabled,
            "has_api_key": bool(llm_config.api_key),
            "base_url": llm_config.base_url,
            "model_info": {
                "family": llm_config.model_info.family,
                "vision": llm_config.model_info.vision,
                "function_calling": llm_config.model_info.function_calling,
                "json_output": llm_config.model_info.json_output,
                "structured_output": llm_config.model_info.structured_output,
            } if llm_config.model_info else {},
            "cached": name in self._models
        }
    
    def clear_cache(self) -> None:
        """Clear the LLM model cache.
        
        This forces the factory to recreate models on next access,
        useful for configuration changes.
        """
        self._models.clear()
    
    def reload_settings(self, config_file: Optional[str] = None) -> None:
        """Reload settings and clear cache.
        
        Args:
            config_file: Optional path to a new configuration file.
        """
        self.settings = Settings(config_file)
        self.clear_cache()
    
    def _create_model(self, config: LLMProviderConfig) -> BaseChatModel:
        """Create a LangChain model from configuration.
        
        Args:
            config: LLM provider configuration.
            
        Returns:
            Configured LangChain chat model.
            
        Raises:
            ValueError: If the provider type is not supported.
        """
        provider_type = config.type.lower()
        
        # Common model parameters
        model_params = {
            "model": config.model_name,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }
        
        if provider_type == "openai":
            # Handle custom base URL for OpenAI-compatible APIs
            if config.base_url:
                model_params["base_url"] = config.base_url
            
            return ChatOpenAI(
                api_key=config.api_key,
                max_retries=3,
                request_timeout=60,
                **model_params
            )
            
        elif provider_type == "deepseek":
            return ChatDeepSeek(
                api_key=config.api_key,
                max_retries=3,
                request_timeout=60,
                **model_params
            )
        
        elif provider_type == "anthropic":
            return ChatAnthropic(
                api_key=config.api_key,
                max_retries=3,
                timeout=60,
                **model_params
            )
        
        elif provider_type == "ollama":
            
            # Handle custom base URL for Ollama
            if config.base_url:
                model_params["base_url"] = config.base_url
                            
            if config.max_tokens:
                model_params["num_predict"] = config.max_tokens
                
            config.validate_model_on_init = True
            #config.format = "json"
            
            return ChatOllama(
                **model_params
            )
        
        else:
            # Try using LangChain's universal init_chat_model for other providers
            try:
                init_params = model_params.copy()
                if config.api_key:
                    init_params["api_key"] = config.api_key
                if config.base_url:
                    init_params["base_url"] = config.base_url
                
                return init_chat_model(**init_params)
            except Exception as e:
                raise ValueError(f"Unsupported LLM provider type: {provider_type}") from e
    
    def create_structured_llm(self, name: Optional[str] = None, pydantic_object: Optional[Any] = None) -> BaseChatModel:
        """Create an LLM with structured output capability.
        
        Args:
            name: The name of the LLM provider. If None, uses default.
            pydantic_object: Pydantic model class for structured output.
            
        Returns:
            LLM configured for structured output.
            
        Example:
            >>> from pydantic import BaseModel
            >>> class MySchema(BaseModel):
            ...     answer: str
            >>> factory = LLMFactory()
            >>> structured_llm = factory.create_structured_llm("openai", MySchema)
        """
        llm = self.get_llm(name)
        
        if pydantic_object is not None:
            return llm.with_structured_output(pydantic_object)
        
        return llm
    
    def create_tool_enabled_llm(self, name: Optional[str] = None, tools: Optional[List[Any]] = None) -> BaseChatModel:
        """Create an LLM with tool calling capability.
        
        Args:
            name: The name of the LLM provider. If None, uses default.
            tools: List of tools to bind to the LLM.
            
        Returns:
            LLM configured for tool calling.
            
        Example:
            >>> from langchain.tools import tool
            >>> @tool
            >>> def get_weather(city: str) -> str:
            ...     return f"Weather in {city}"
            >>> factory = LLMFactory()
            >>> tool_llm = factory.create_tool_enabled_llm("openai", [get_weather])
        """
        llm = self.get_llm(name)
        
        if tools is not None:
            return llm.bind_tools(tools)
        
        return llm
    
    def create_llm_with_callbacks(
        self, 
        name: Optional[str] = None, 
        callbacks: Optional[List[BaseCallbackHandler]] = None
    ) -> BaseChatModel:
        """Create an LLM with callback handlers for tracing.
        
        Args:
            name: The name of the LLM provider. If None, uses default.
            callbacks: List of callback handlers to attach to the LLM.
            
        Returns:
            LLM configured with callback handlers.
            
        Example:
            >>> from ..observability.langfuse_callback import LangfuseCallbackHandler
            >>> factory = LLMFactory()
            >>> tracer = make_tracer(tracer_config)
            >>> callback = LangfuseCallbackHandler(tracer)
            >>> llm = factory.create_llm_with_callbacks("openai", [callback])
        """
        llm = self.get_llm(name)
        
        if callbacks is not None:
            # Set callbacks on the LLM
            llm.callbacks = callbacks
            return llm
        
        return llm
    
    def create_structured_llm_with_callbacks(
        self, 
        name: Optional[str] = None, 
        pydantic_object: Optional[Any] = None,
        callbacks: Optional[List[BaseCallbackHandler]] = None
    ) -> BaseChatModel:
        """Create a structured LLM with callback handlers for tracing.
        
        Args:
            name: The name of the LLM provider. If None, uses default.
            pydantic_object: Pydantic model class for structured output.
            callbacks: List of callback handlers to attach to the LLM.
            
        Returns:
            Structured LLM configured with callback handlers.
            
        Example:
            >>> from ..observability.langfuse_callback import LangfuseCallbackHandler
            >>> from pydantic import BaseModel
            >>> class MySchema(BaseModel):
            ...     answer: str
            >>> factory = LLMFactory()
            >>> tracer = make_tracer(tracer_config)
            >>> callback = LangfuseCallbackHandler(tracer)
            >>> llm = factory.create_structured_llm_with_callbacks("openai", MySchema, [callback])
        """
        llm = self.create_structured_llm(name, pydantic_object)
        
        if callbacks is not None:
            # Set callbacks on the LLM
            llm.callbacks = callbacks
            return llm
        
        return llm
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all configured LLMs.
        
        Returns:
            Dictionary with health status of each LLM provider.
        """
        health_status = {}
        
        for llm_name in self.list_available_llms():
            try:
                llm = self.get_llm(llm_name)
                # Simple test to check if the model is accessible
                response = llm.invoke("Hello")
                health_status[llm_name] = {
                    "status": "healthy",
                    "response_length": len(str(response.content)) if hasattr(response, 'content') else 0
                }
            except Exception as e:
                health_status[llm_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        return health_status


# Global factory instance
llm_factory = LLMFactory()
