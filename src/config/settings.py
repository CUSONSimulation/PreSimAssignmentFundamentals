"""Configuration management for HeyGen Streamlit Avatar application."""

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # HeyGen API Configuration
    heygen_api_key: str = Field(..., env="HEYGEN_API_KEY")
    knowledge_base_id: str = Field("6bbcea1ca7ab4640a7802da4d1492e62", env="KNOWLEDGE_BASE_ID")
    avatar_id: str = Field("Rika_Chair_Sitting_public", env="AVATAR_ID")
    
    # API Endpoints
    heygen_base_url: str = "https://api.heygen.com/v1"
    
    # Session Configuration
    session_timeout: int = Field(120, env="SESSION_TIMEOUT")
    max_concurrent_sessions: int = Field(3, env="MAX_CONCURRENT_SESSIONS")
    keep_alive_interval: int = 30
    
    # WebRTC Configuration
    turn_server_url: str = Field("stun:stun.l.google.com:19302", env="TURN_SERVER_URL")
    ice_servers: List[dict] = [{"urls": ["stun:stun.l.google.com:19302"]}]
    
    # Redis Configuration
    redis_url: Optional[str] = Field(None, env="REDIS_URL")
    
    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    # Security
    cors_origins: List[str] = Field(["https://localhost:8501"], env="CORS_ORIGINS")
    
    # Avatar Configuration
    avatar_quality: str = "high"  # high, medium, low
    voice_emotion: str = "excited"  # excited, serious, friendly
    speaking_rate: float = 1.0
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }

# Global settings instance
settings = Settings()