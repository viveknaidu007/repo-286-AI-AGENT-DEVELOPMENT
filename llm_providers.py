"""
LLM Provider abstractions for Google Gemini, OpenAI, and Azure OpenAI.
Default is Google Gemini (free), with commented code for switching providers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import logging

# Google Gemini (Default)
import google.generativeai as genai

# OpenAI (Uncomment to use)
# from openai import OpenAI

# LangChain imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# For OpenAI via LangChain (Uncomment to use)
# from langchain_openai import ChatOpenAI, AzureChatOpenAI

from config import get_settings

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Base class for LLM providers."""
    
    @abstractmethod
    def generate_response(
        self, 
        prompt: str, 
        system_message: str = "",
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    def generate_with_tools(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        system_message: str = ""
    ) -> Dict[str, Any]:
        """Generate a response with tool calling capability."""
        pass


class GoogleGeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider (Default - Free)."""
    
    def __init__(self):
        settings = get_settings()
        genai.configure(api_key=settings.google_api_key)
        
        # Using LangChain for consistency
        self.llm = ChatGoogleGenerativeAI(
            model=settings.google_model,
            google_api_key=settings.google_api_key,
            temperature=0.7,
            convert_system_message_to_human=True
        )
        logger.info("Initialized Google Gemini provider")
    
    def generate_response(
        self, 
        prompt: str, 
        system_message: str = "",
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """Generate a response using Google Gemini."""
        messages = []
        
        if system_message:
            messages.append(SystemMessage(content=system_message))
        
        # Add conversation history if provided
        if conversation_history:
            for msg in conversation_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        messages.append(HumanMessage(content=prompt))
        
        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Error generating response with Gemini: {e}")
            raise
    
    def generate_with_tools(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        system_message: str = ""
    ) -> Dict[str, Any]:
        """Generate response with tool calling (simplified for Gemini)."""
        # Note: Gemini's tool calling is different from OpenAI
        # This is a simplified implementation
        messages = []
        
        if system_message:
            messages.append(SystemMessage(content=system_message))
        
        # Add tool descriptions to the prompt
        tool_descriptions = "\n".join([
            f"- {tool['name']}: {tool['description']}"
            for tool in tools
        ])
        
        enhanced_prompt = f"{prompt}\n\nAvailable tools:\n{tool_descriptions}"
        messages.append(HumanMessage(content=enhanced_prompt))
        
        try:
            response = self.llm.invoke(messages)
            return {
                "response": response.content,
                "tool_calls": []  # Simplified - parse from response if needed
            }
        except Exception as e:
            logger.error(f"Error with tool calling in Gemini: {e}")
            raise


# Uncomment below to use OpenAI
"""
class OpenAIProvider(BaseLLMProvider):
    '''OpenAI LLM provider.'''
    
    def __init__(self):
        settings = get_settings()
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.7
        )
        logger.info("Initialized OpenAI provider")
    
    def generate_response(
        self, 
        prompt: str, 
        system_message: str = "",
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        '''Generate a response using OpenAI.'''
        messages = []
        
        if system_message:
            messages.append(SystemMessage(content=system_message))
        
        if conversation_history:
            for msg in conversation_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        messages.append(HumanMessage(content=prompt))
        
        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Error generating response with OpenAI: {e}")
            raise
    
    def generate_with_tools(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        system_message: str = ""
    ) -> Dict[str, Any]:
        '''Generate response with tool calling.'''
        # Convert tools to OpenAI format
        openai_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool.get("parameters", {})
                }
            }
            for tool in tools
        ]
        
        messages = []
        if system_message:
            messages.append(SystemMessage(content=system_message))
        messages.append(HumanMessage(content=prompt))
        
        try:
            llm_with_tools = self.llm.bind_tools(openai_tools)
            response = llm_with_tools.invoke(messages)
            
            tool_calls = []
            if hasattr(response, 'tool_calls') and response.tool_calls:
                tool_calls = [
                    {
                        "name": tc.name,
                        "arguments": tc.args
                    }
                    for tc in response.tool_calls
                ]
            
            return {
                "response": response.content,
                "tool_calls": tool_calls
            }
        except Exception as e:
            logger.error(f"Error with tool calling in OpenAI: {e}")
            raise
"""


# Uncomment below to use Azure OpenAI
"""
class AzureOpenAIProvider(BaseLLMProvider):
    '''Azure OpenAI LLM provider.'''
    
    def __init__(self):
        settings = get_settings()
        self.llm = AzureChatOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            deployment_name=settings.azure_openai_deployment_name,
            temperature=0.7
        )
        logger.info("Initialized Azure OpenAI provider")
    
    def generate_response(
        self, 
        prompt: str, 
        system_message: str = "",
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        '''Generate a response using Azure OpenAI.'''
        messages = []
        
        if system_message:
            messages.append(SystemMessage(content=system_message))
        
        if conversation_history:
            for msg in conversation_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        messages.append(HumanMessage(content=prompt))
        
        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Error generating response with Azure OpenAI: {e}")
            raise
    
    def generate_with_tools(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        system_message: str = ""
    ) -> Dict[str, Any]:
        '''Generate response with tool calling.'''
        # Azure OpenAI uses same format as OpenAI
        openai_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool.get("parameters", {})
                }
            }
            for tool in tools
        ]
        
        messages = []
        if system_message:
            messages.append(SystemMessage(content=system_message))
        messages.append(HumanMessage(content=prompt))
        
        try:
            llm_with_tools = self.llm.bind_tools(openai_tools)
            response = llm_with_tools.invoke(messages)
            
            tool_calls = []
            if hasattr(response, 'tool_calls') and response.tool_calls:
                tool_calls = [
                    {
                        "name": tc.name,
                        "arguments": tc.args
                    }
                    for tc in response.tool_calls
                ]
            
            return {
                "response": response.content,
                "tool_calls": tool_calls
            }
        except Exception as e:
            logger.error(f"Error with tool calling in Azure OpenAI: {e}")
            raise
"""


def get_llm_provider() -> BaseLLMProvider:
    """Factory function to get the configured LLM provider."""
    settings = get_settings()
    
    if settings.llm_provider == "google":
        return GoogleGeminiProvider()
    # Uncomment below when using OpenAI
    # elif settings.llm_provider == "openai":
    #     return OpenAIProvider()
    # Uncomment below when using Azure OpenAI
    # elif settings.llm_provider == "azure_openai":
    #     return AzureOpenAIProvider()
    else:
        raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
