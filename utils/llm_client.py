"""
LLM client using LangChain ChatOpenAI for Qwen API.

Provides async support and tools calling capability, integrated with LangGraph ecosystem.
"""

import asyncio
from typing import Any
from pydantic import BaseModel, SecretStr

from langchain_qwq import ChatQwen
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langchain_core.tools import BaseTool

from config.settings import get_settings
from utils.logger import get_agent_logger

logger = get_agent_logger()


class LLMClient:
    """
    LLM client using LangChain ChatOpenAI.
    
    Supports:
    - Sync and async chat completion
    - Structured output with Pydantic models
    - Tools/function calling
    - Retry with exponential backoff
    """
    
    def __init__(
        self,
        api_key: str | None = None,
        api_base: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_retries: int | None = None,
        timeout: int | None = None
    ):
        """
        Initialize LLM client.
        
        Args:
            api_key: API key (defaults to settings)
            api_base: API base URL (defaults to settings)
            model: Model name (defaults to settings)
            temperature: Generation temperature (defaults to settings)
            max_retries: Maximum retry attempts (defaults to settings)
            timeout: Request timeout in seconds (defaults to settings)
        """
        settings = get_settings()
        
        self.api_key = SecretStr(api_key or settings.api_key)
        self.api_base = api_base or settings.api_base
        self.model = model or settings.model_name
        self.temperature = temperature if temperature is not None else settings.temperature
        self.max_retries = max_retries if max_retries is not None else settings.max_retries
        self.timeout = timeout if timeout is not None else settings.timeout
        
        # Initialize ChatOpenAI client
        self._chat = ChatQwen(
            api_key=self.api_key,
            base_url=self.api_base,
            model=self.model,
            temperature=self.temperature,
            max_retries=self.max_retries,
            timeout=self.timeout,
        )
        
        logger.info("Initialized LLM client with model: %s", self.model)
    
    @property
    def chat(self) -> ChatQwen:
        """Get the underlying ChatQwen instance."""
        return self._chat
    
    def _build_messages(self, messages: list[dict[str, str]]) -> list[BaseMessage]:
        """Convert dict messages to LangChain message objects."""
        result = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                result.append(SystemMessage(content=content))
            elif role == "assistant" or role == "ai":
                result.append(AIMessage(content=content))
            else:
                result.append(HumanMessage(content=content))
        
        return result
    
    def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        **kwargs
    ) -> str:
        """
        Synchronous chat completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            **kwargs: Additional parameters
            
        Returns:
            Generated text response
        """
        lc_messages = self._build_messages(messages)
        
        chat = self._chat
        if temperature is not None:
            chat = self._chat.with_config(configurable={"temperature": temperature})
        
        response = chat.invoke(lc_messages, **kwargs)
        return response.content  # type: ignore
    
    async def achat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        **kwargs
    ) -> str:
        """
        Asynchronous chat completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            **kwargs: Additional parameters
            
        Returns:
            Generated text response
        """
        lc_messages = self._build_messages(messages)
        
        chat = self._chat
        if temperature is not None:
            chat = self._chat.with_config(configurable={"temperature": temperature})
        
        response = await chat.ainvoke(lc_messages, **kwargs)
        return response.content  # type: ignore
    
    def bind_tools(self, tools: list[BaseTool | type[BaseModel] | dict]) -> ChatQwen:
        """
        Bind tools to the chat model for function calling.
        
        Args:
            tools: List of tools (LangChain tools, Pydantic models, or dicts)
            
        Returns:
            ChatQwen instance with tools bound
        """
        return self._chat.bind_tools(tools)  # type: ignore
    
    async def astructured_completion[T: BaseModel](
        self,
        schema: type[T],
        messages: list[dict[str, str]],
        **kwargs
    ) -> T:
        """
        Async chat completion with structured Pydantic output.
        
        Args:
            schema: Pydantic model class for the output
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional parameters
            
        Returns:
            Pydantic model instance with parsed response
        """
        lc_messages = self._build_messages(messages)
        structured_llm = self.chat.with_structured_output(schema, **kwargs)
        return await structured_llm.ainvoke(lc_messages) # type: ignore
    
    def structured_completion[T](
        self,
        schema: type[T],
        messages: list[dict[str, str]],
        **kwargs
    ) -> T:
        """
        Sync chat completion with structured Pydantic output.
        
        Args:
            schema: Pydantic model class for the output
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional parameters
            
        Returns:
            Pydantic model instance with parsed response
        """
        lc_messages = self._build_messages(messages)
        structured_llm = self.chat.with_structured_output(schema, **kwargs)
        return structured_llm.invoke(lc_messages)  # type: ignore


# Global LLM client instance
_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Get the global LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


def reset_llm_client() -> None:
    """Reset the global LLM client (useful for testing)."""
    global _llm_client
    _llm_client = None


async def batch_async_calls(
    coroutines: list,
    max_concurrency: int = 10
) -> list[Any]:
    """
    Execute multiple async calls with concurrency limit.
    
    Args:
        coroutines: List of coroutines to execute
        max_concurrency: Maximum concurrent executions
        
    Returns:
        List of results in same order as input
    """
    semaphore = asyncio.Semaphore(max_concurrency)
    
    async def bounded_call(coro):
        async with semaphore:
            return await coro
    
    return await asyncio.gather(*[bounded_call(c) for c in coroutines])
