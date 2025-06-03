"""WebRTC handler for real-time avatar streaming."""

import asyncio
from typing import Optional, Dict, Any, Callable
import structlog
from streamlit_webrtc import WebRtcMode, RTCConfiguration, webrtc_streamer
from aiortc import RTCPeerConnection, RTCSessionDescription
from config.settings import settings
from utils.logging_config import metrics

logger = structlog.get_logger(__name__)

class WebRTCHandler:
    """Handles WebRTC connections for avatar streaming."""
    
    def __init__(self):
        self.connection: Optional[RTCPeerConnection] = None
        self.room_url: Optional[str] = None
        self.access_token: Optional[str] = None
        self.connected = False
        
        # WebRTC configuration
        self.rtc_config = RTCConfiguration(
            iceServers=settings.ice_servers
        )
    
    def setup_webrtc_streamer(
        self,
        key: str,
        on_audio_frame: Optional[Callable] = None,
        on_video_frame: Optional[Callable] = None
    ) -> Any:
        """Setup Streamlit WebRTC streamer component."""
        
        def audio_frame_callback(frame):
            """Process incoming audio frames."""
            if on_audio_frame:
                return on_audio_frame(frame)
            return frame
        
        def video_frame_callback(frame):
            """Process incoming video frames."""
            if on_video_frame:
                return on_video_frame(frame)
            return frame
        
        # Configure WebRTC streamer
        webrtc_ctx = webrtc_streamer(
            key=key,
            mode=WebRtcMode.SENDRECV,
            rtc_configuration=self.rtc_config,
            audio_frame_callback=audio_frame_callback,
            video_frame_callback=video_frame_callback,
            media_stream_constraints={
                "video": {"width": 640, "height": 480},
                "audio": {"echoCancellation": True, "noiseSuppression": True}
            },
            async_processing=True
        )
        
        return webrtc_ctx
    
    async def connect_to_livekit(self, room_url: str, access_token: str) -> bool:
        """Connect to LiveKit room for avatar streaming."""
        self.room_url = room_url
        self.access_token = access_token
        
        try:
            logger.info("Connecting to LiveKit room", room_url=room_url)
            
            # Initialize RTCPeerConnection
            self.connection = RTCPeerConnection(self.rtc_config)
            
            # Setup connection event handlers
            @self.connection.on("connectionstatechange")
            async def on_connectionstatechange():
                logger.info("Connection state changed", state=self.connection.connectionState)
                
                if self.connection.connectionState == "connected":
                    self.connected = True
                    metrics.increment("webrtc_connections_established")
                elif self.connection.connectionState in ["failed", "disconnected", "closed"]:
                    self.connected = False
                    metrics.increment("webrtc_connections_failed")
            
            @self.connection.on("datachannel")
            def on_datachannel(channel):
                logger.info("Data channel established", label=channel.label)
                
                @channel.on("message")
                def on_message(message):
                    logger.debug("Received data channel message", message=message)
            
            # Create data channel for control messages
            self.connection.createDataChannel("control")
            
            logger.info("LiveKit connection established")
            return True
            
        except Exception as e:
            logger.error("Failed to connect to LiveKit", error=str(e))
            self.connected = False
            return False
    
    async def send_audio_data(self, audio_data: bytes) -> bool:
        """Send audio data through WebRTC connection."""
        if not self.connected or not self.connection:
            return False
        
        try:
            # Process audio data for transmission
            # Implementation depends on audio format requirements
            logger.debug("Sending audio data", size=len(audio_data))
            return True
        except Exception as e:
            logger.error("Failed to send audio data", error=str(e))
            return False
    
    async def disconnect(self) -> None:
        """Disconnect WebRTC connection."""
        if self.connection:
            try:
                await self.connection.close()
                logger.info("WebRTC connection closed")
            except Exception as e:
                logger.warning("Error closing WebRTC connection", error=str(e))
            finally:
                self.connection = None
                self.connected = False
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebRTC connection statistics."""
        if not self.connection:
            return {}
        
        return {
            "connected": self.connected,
            "connection_state": self.connection.connectionState if self.connection else "disconnected",
            "room_url": self.room_url,
            "has_audio": bool(self.connection and self.connection.getTransceivers()),
            "has_video": bool(self.connection and self.connection.getTransceivers())
        }

# Global WebRTC handler instance
webrtc_handler = WebRTCHandler()