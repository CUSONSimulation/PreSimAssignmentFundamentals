"""HeyGen API client with authentication and session management."""

import asyncio
import time
from typing import Optional, Dict, Any
import httpx
import structlog
from config.settings import settings
from utils.error_handlers import handle_api_errors, HeyGenAPIError, SessionLimitError
from utils.logging_config import metrics

logger = structlog.get_logger(__name__)

class HeyGenClient:
    """HeyGen API client for avatar interactions."""
    
    def __init__(self):
        self.api_key = settings.heygen_api_key
        self.base_url = settings.heygen_base_url
        self.session_token: Optional[str] = None
        self.session_id: Optional[str] = None
        self.session_active = False
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            headers={"x-api-key": self.api_key}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
    
    @handle_api_errors
    async def generate_session_token(self) -> str:
        """Generate a session token from API key."""
        logger.info("Generating session token")
        
        response = await self._client.post(
            f"{self.base_url}/streaming.session_token",
            headers={"x-api-key": self.api_key}
        )
        response.raise_for_status()
        
        data = response.json()
        self.session_token = data["token"]
        
        logger.info("Session token generated successfully")
        metrics.increment("session_tokens_generated")
        
        return self.session_token
    
    @handle_api_errors
    async def create_session(self, quality: str = "high") -> Dict[str, Any]:
        """Create a new streaming session."""
        logger.info("Creating streaming session", quality=quality)
        
        if not self.session_token:
            await self.generate_session_token()
        
        payload = {
            "quality": quality,
            "avatar_name": settings.avatar_id,
            "voice": {
                "voice_id": "claire",
                "rate": settings.speaking_rate,
                "emotion": settings.voice_emotion
            },
            "knowledge_base_id": settings.knowledge_base_id,
            "version": "v2"
        }
        
        response = await self._client.post(
            f"{self.base_url}/streaming.create_session",
            json=payload,
            headers={"Authorization": f"Bearer {self.session_token}"}
        )
        
        if response.status_code == 400:
            error_data = response.json()
            if "concurrent session limit" in str(error_data).lower():
                raise SessionLimitError("Concurrent session limit reached", 400, error_data)
        
        response.raise_for_status()
        data = response.json()
        
        self.session_id = data["session_id"]
        
        logger.info("Streaming session created", session_id=self.session_id)
        metrics.increment("sessions_created")
        
        return data
    
    @handle_api_errors
    async def start_session(self) -> Dict[str, Any]:
        """Start the streaming session."""
        if not self.session_id:
            raise HeyGenAPIError("No session ID available. Create session first.")
        
        logger.info("Starting streaming session", session_id=self.session_id)
        
        response = await self._client.post(
            f"{self.base_url}/streaming.start_session",
            json={"session_id": self.session_id},
            headers={"Authorization": f"Bearer {self.session_token}"}
        )
        response.raise_for_status()
        
        data = response.json()
        self.session_active = True
        
        logger.info("Streaming session started successfully")
        metrics.increment("sessions_started")
        
        return data
    
    @handle_api_errors
    async def send_task(self, text: str, task_type: str = "talk") -> bool:
        """Send a task to the avatar."""
        if not self.session_active:
            raise HeyGenAPIError("Session not active. Start session first.")
        
        logger.info("Sending task to avatar", task_type=task_type, text_length=len(text))
        
        payload = {
            "session_id": self.session_id,
            "text": text,
            "task_type": task_type
        }
        
        response = await self._client.post(
            f"{self.base_url}/streaming.task",
            json=payload,
            headers={"Authorization": f"Bearer {self.session_token}"}
        )
        response.raise_for_status()
        
        logger.info("Task sent successfully")
        metrics.increment("tasks_sent")
        
        return True
    
    @handle_api_errors
    async def stop_session(self) -> bool:
        """Stop the streaming session."""
        if not self.session_id:
            return True
        
        logger.info("Stopping streaming session", session_id=self.session_id)
        
        try:
            response = await self._client.post(
                f"{self.base_url}/streaming.stop_session",
                json={"session_id": self.session_id},
                headers={"Authorization": f"Bearer {self.session_token}"}
            )
            response.raise_for_status()
        except Exception as e:
            logger.warning("Error stopping session", error=str(e))
        
        self.session_active = False
        self.session_id = None
        
        logger.info("Session stopped")
        metrics.increment("sessions_stopped")
        
        return True
    
    @handle_api_errors
    async def get_session_info(self) -> Dict[str, Any]:
        """Get current session information."""
        if not self.session_id:
            raise HeyGenAPIError("No active session")
        
        response = await self._client.get(
            f"{self.base_url}/streaming.session_info",
            params={"session_id": self.session_id},
            headers={"Authorization": f"Bearer {self.session_token}"}
        )
        response.raise_for_status()
        
        return response.json()
    
    async def keep_session_alive(self) -> None:
        """Keep the session alive with periodic pings."""
        while self.session_active:
            try:
                await self.get_session_info()
                logger.debug("Session keep-alive ping sent")
            except Exception as e:
                logger.warning("Keep-alive failed", error=str(e))
            
            await asyncio.sleep(settings.keep_alive_interval)