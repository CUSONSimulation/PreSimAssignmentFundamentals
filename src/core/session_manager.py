"""Session management with state persistence and lifecycle handling."""

import asyncio
import time
import json
from typing import Optional, Dict, Any
import structlog
from config.settings import settings
from utils.logging_config import metrics

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = structlog.get_logger(__name__)

class SessionManager:
    """Manages avatar session lifecycle and state persistence."""
    
    def __init__(self):
        self.redis_client: Optional[Any] = None
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeouts: Dict[str, float] = {}
        
        if REDIS_AVAILABLE and settings.redis_url:
            try:
                self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
                self.redis_client.ping()
                logger.info("Redis connection established")
            except Exception as e:
                logger.warning("Redis connection failed, using in-memory storage", error=str(e))
                self.redis_client = None
    
    async def create_session(self, user_id: str, session_data: Dict[str, Any]) -> str:
        """Create a new session with persistence."""
        session_id = f"session_{user_id}_{int(time.time())}"
        
        session_info = {
            "id": session_id,
            "user_id": user_id,
            "created_at": time.time(),
            "last_activity": time.time(),
            "data": session_data,
            "active": True
        }
        
        # Store session
        if self.redis_client:
            try:
                await asyncio.to_thread(
                    self.redis_client.setex,
                    f"session:{session_id}",
                    settings.session_timeout,
                    json.dumps(session_info)
                )
            except Exception as e:
                logger.warning("Redis storage failed", error=str(e))
                self.sessions[session_id] = session_info
        else:
            self.sessions[session_id] = session_info
        
        # Set timeout
        self.session_timeouts[session_id] = time.time() + settings.session_timeout
        
        logger.info("Session created", session_id=session_id, user_id=user_id)
        metrics.increment("sessions_created_total")
        
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data."""
        if self.redis_client:
            try:
                data = await asyncio.to_thread(
                    self.redis_client.get,
                    f"session:{session_id}"
                )
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.warning("Redis retrieval failed", error=str(e))
        
        return self.sessions.get(session_id)
    
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session data."""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        session["last_activity"] = time.time()
        session["data"].update(updates)
        
        # Update storage
        if self.redis_client:
            try:
                await asyncio.to_thread(
                    self.redis_client.setex,
                    f"session:{session_id}",
                    settings.session_timeout,
                    json.dumps(session)
                )
            except Exception as e:
                logger.warning("Redis update failed", error=str(e))
                self.sessions[session_id] = session
        else:
            self.sessions[session_id] = session
        
        logger.debug("Session updated", session_id=session_id)
        return True
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if self.redis_client:
            try:
                await asyncio.to_thread(
                    self.redis_client.delete,
                    f"session:{session_id}"
                )
            except Exception as e:
                logger.warning("Redis deletion failed", error=str(e))
        
        self.sessions.pop(session_id, None)
        self.session_timeouts.pop(session_id, None)
        
        logger.info("Session deleted", session_id=session_id)
        metrics.increment("sessions_deleted_total")
        
        return True
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        current_time = time.time()
        expired_sessions = []
        
        # Check timeouts
        for session_id, timeout in self.session_timeouts.items():
            if current_time > timeout:
                expired_sessions.append(session_id)
        
        # Clean up expired sessions
        for session_id in expired_sessions:
            await self.delete_session(session_id)
        
        if expired_sessions:
            logger.info("Cleaned up expired sessions", count=len(expired_sessions))
        
        return len(expired_sessions)
    
    async def get_active_session_count(self, user_id: Optional[str] = None) -> int:
        """Get count of active sessions."""
        count = 0
        
        if self.redis_client:
            try:
                keys = await asyncio.to_thread(
                    self.redis_client.keys,
                    "session:*"
                )
                for key in keys:
                    data = await asyncio.to_thread(self.redis_client.get, key)
                    if data:
                        session = json.loads(data)
                        if session.get("active") and (not user_id or session.get("user_id") == user_id):
                            count += 1
            except Exception as e:
                logger.warning("Redis count failed", error=str(e))
                # Fallback to in-memory count
                for session in self.sessions.values():
                    if session.get("active") and (not user_id or session.get("user_id") == user_id):
                        count += 1
        else:
            for session in self.sessions.values():
                if session.get("active") and (not user_id or session.get("user_id") == user_id):
                    count += 1
        
        return count
    
    async def can_create_session(self, user_id: str) -> bool:
        """Check if user can create a new session."""
        active_count = await self.get_active_session_count(user_id)
        return active_count < settings.max_concurrent_sessions

# Global session manager instance
session_manager = SessionManager()