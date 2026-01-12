"""
Configuration management for the RAG AI Agent.
Loads environment variables and provides centralized config access.
"""

import os
from typing import Literal
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # LLM Provider Configuration
    llm_provider: Literal["google", "openai", "azure_openai"] = Field(
        default="google",
        description="LLM provider to use"
    )
    
    # Google AI (Gemini)
    google_api_key: str = Field(default="", description="Google AI API key")
    google_model: str = Field(default="gemini-pro", description="Google model name")
    
    # OpenAI
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_model: str = Field(default="gpt-4", description="OpenAI model name")
    
    # Azure OpenAI
    azure_openai_api_key: str = Field(default="", description="Azure OpenAI API key")
    azure_openai_endpoint: str = Field(default="", description="Azure OpenAI endpoint")
    azure_openai_deployment_name: str = Field(default="", description="Azure deployment name")
    azure_openai_api_version: str = Field(
        default="2024-02-15-preview",
        description="Azure OpenAI API version"
    )
    
    # Vector Store Configuration
    vector_store: Literal["faiss", "pinecone", "azure_search"] = Field(
        default="faiss",
        description="Vector store to use"
    )
    
    # FAISS
    faiss_index_path: str = Field(
        default="./vector_store/faiss_index",
        description="Path to FAISS index"
    )
    
    # Pinecone
    pinecone_api_key: str = Field(default="", description="Pinecone API key")
    pinecone_environment: str = Field(default="", description="Pinecone environment")
    pinecone_index_name: str = Field(default="rag-documents", description="Pinecone index name")
    
    # Azure AI Search
    azure_search_endpoint: str = Field(default="", description="Azure Search endpoint")
    azure_search_api_key: str = Field(default="", description="Azure Search API key")
    azure_search_index_name: str = Field(
        default="rag-documents",
        description="Azure Search index name"
    )
    
    # Application Settings
    app_name: str = Field(default="RAG AI Agent", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    
    # Document Processing
    chunk_size: int = Field(default=1000, description="Document chunk size")
    chunk_overlap: int = Field(default=200, description="Chunk overlap size")
    max_chunks_to_retrieve: int = Field(
        default=5,
        description="Maximum chunks to retrieve for context"
    )
    
    # Session Configuration
    session_timeout: int = Field(default=3600, description="Session timeout in seconds")
    max_conversation_history: int = Field(
        default=10,
        description="Max conversation turns to keep in memory"
    )
    
    # CORS Settings
    allowed_origins: str = Field(
        default="http://localhost:8000,http://127.0.0.1:8000",
        description="Allowed CORS origins (comma-separated)"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def get_allowed_origins_list(self) -> list[str]:
        """Parse allowed origins into a list."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    def validate_llm_config(self) -> bool:
        """Validate that required LLM provider credentials are present."""
        if self.llm_provider == "google":
            return bool(self.google_api_key)
        elif self.llm_provider == "openai":
            return bool(self.openai_api_key)
        elif self.llm_provider == "azure_openai":
            return bool(
                self.azure_openai_api_key 
                and self.azure_openai_endpoint 
                and self.azure_openai_deployment_name
            )
        return False
    
    def validate_vector_store_config(self) -> bool:
        """Validate that required vector store credentials are present."""
        if self.vector_store == "faiss":
            return True  # FAISS doesn't need credentials
        elif self.vector_store == "pinecone":
            return bool(self.pinecone_api_key and self.pinecone_environment)
        elif self.vector_store == "azure_search":
            return bool(self.azure_search_endpoint and self.azure_search_api_key)
        return False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings
