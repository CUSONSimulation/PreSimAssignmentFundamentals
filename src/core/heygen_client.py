"""HeyGen API client with authentication and session management - WITH DEBUG LOGGING."""

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
            f"{self.base_url}/streaming.create_token",
            headers={"x-api-key": self.api_key}
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Correct response structure - token is nested in data
        if "data" in data and "token" in data["data"]:
            self.session_token = data["data"]["token"]
        else:
            # Fallback: log the actual response structure for debugging
            logger.error("Unexpected token response structure", response_data=data)
            raise HeyGenAPIError(f"Token not found in response: {data}")
        
        logger.info("Session token generated successfully")
        metrics.increment("session_tokens_generated")
        
        return self.session_token
    
    @handle_api_errors
    async def create_session(self, quality: str = "high") -> Dict[str, Any]:
        """Create a new streaming session."""
        logger.info("Creating streaming session", quality=quality)
        
        if not self.session_token:
            await self.generate_session_token()
        
        # FIXED: Updated payload structure
        payload = {
            "version": "v2",
            "avatar_id": settings.avatar_id,
            "quality": quality,
        }
        
        # Add voice configuration if specified
        if hasattr(settings, 'voice_id') and settings.voice_id:
            payload["voice"] = {
                "voice_id": settings.voice_id,
                "rate": settings.speaking_rate,
                "emotion": settings.voice_emotion
            }
        
        # Add knowledge base if specified
        if hasattr(settings, 'knowledge_base_id') and settings.knowledge_base_id:
            payload["knowledge_id"] = settings.knowledge_base_id
        
        # Log the payload for debugging
        logger.info("Session payload", payload=payload)
        
        response = await self._client.post(
            f"{self.base_url}/streaming.new",
            json=payload,
            headers={"Authorization": f"Bearer {self.session_token}"}
        )
        
        # Better error handling for 400 responses
        if response.status_code == 400:
            try:
                error_data = response.json()
                logger.error("Session creation failed", status_code=400, error_data=error_data)
                
                if "voice_not_found" in str(error_data).lower():
                    raise HeyGenAPIError(
                        "Voice ID not found. Please check your voice_id in settings or remove it to use the avatar's default voice.", 
                        400, 
                        error_data
                    )
                elif "concurrent session limit" in str(error_data).lower():
                    raise SessionLimitError("Concurrent session limit reached", 400, error_data)
                else:
                    raise HeyGenAPIError(f"Bad request: {error_data}", 400, error_data)
            except Exception as e:
                # If we can't parse the error response
                error_text = response.text
                logger.error("Session creation failed with unparseable response", 
                           status_code=400, response_text=error_text)
                raise HeyGenAPIError(f"Bad request: {error_text}", 400)
        
        response.raise_for_status()
        data = response.json()
        
        # DEBUG: Log the full response to understand structure
        logger.info("Create session raw response", response_data=data)
        
        # Handle nested response structure if needed
        if "data" in data:
            session_data = data["data"]
        else:
            session_data = data
        
        self.session_id = session_data.get("session_id")
        
        # DEBUG: Log all keys to see what's available
        logger.info("Session data keys", keys=list(session_data.keys()) if session_data else [])
        
        logger.info("Streaming session created", session_id=self.session_id)
        metrics.increment("sessions_created")
        
        return session_data
    
    @handle_api_errors
    async def start_session(self) -> Dict[str, Any]:
        """Start the streaming session."""
        if not self.session_id:
            raise HeyGenAPIError("No session ID available. Create session first.")
        
        logger.info("Starting streaming session", session_id=self.session_id)
        
        response = await self._client.post(
            f"{self.base_url}/streaming.start",
            json={"session_id": self.session_id},
            headers={"Authorization": f"Bearer {self.session_token}"}
        )
        response.raise_for_status()
        
        data = response.json()
        
        # DEBUG: Log the full response to understand structure
        logger.info("Start session raw response", response_data=data)
        
        # Handle nested response structure
        if "data" in data and isinstance(data["data"], dict):
            start_data = data["data"]
        else:
            start_data = data if isinstance(data, dict) else {}
        
        # Ensure we always return a dictionary
        if not start_data:
            logger.warning("Start session returned empty data")
            start_data = {"session_id": self.session_id, "status": "started"}
        
        # DEBUG: Log what we're returning
        logger.info("Returning start data", start_data=start_data)
            
        self.session_active = True
        
        logger.info("Streaming session started successfully")
        metrics.increment("sessions_started")
        
        return start_data
    
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
                f"{self.base_url}/streaming.stop",
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
