"""Avatar display component with video streaming - FIXED."""

import streamlit as st
from typing import Optional, Dict, Any
import structlog
from core.webrtc_handler import webrtc_handler
from utils.logging_config import metrics

logger = structlog.get_logger(__name__)

class AvatarDisplay:
    """Component for displaying the avatar video stream."""
    
    def __init__(self):
        self.webrtc_ctx = None
        self.connection_status = "disconnected"
    
    def render(self, session_data: Optional[Dict[str, Any]] = None) -> None:
        """Render the avatar display component."""
        
        # Create columns for layout
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("🤖 AI Avatar")
            
            # Video container
            video_container = st.container()
            
            with video_container:
                # FIXED: Check for 'url' instead of 'room_url'
                if session_data and (session_data.get("url") or session_data.get("room_url")):
                    # Log the session data for debugging
                    logger.info("Rendering avatar with session data", 
                              has_url=bool(session_data.get("url")),
                              has_access_token=bool(session_data.get("access_token")),
                              session_id=session_data.get("session_id"))
                    
                    # Get WebRTC connection info
                    room_url = session_data.get("url") or session_data.get("room_url")
                    access_token = session_data.get("access_token")
                    
                    # For HeyGen v2, we need to display using an iframe or WebRTC connection
                    # The avatar should appear through the WebSocket connection
                    
                    # Option 1: Display using iframe with the realtime endpoint
                    if session_data.get("realtime_endpoint"):
                        st.markdown(
                            f"""
                            <div style="position: relative; width: 100%; height: 500px;">
                                <iframe 
                                    src="{session_data['realtime_endpoint']}"
                                    style="width: 100%; height: 100%; border: none; border-radius: 10px;"
                                    allow="camera; microphone; autoplay"
                                ></iframe>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        self.connection_status = "connected"
                        st.success("🟢 Connected to avatar")
                    else:
                        # Option 2: Set up WebRTC connection
                        st.info("🟡 Establishing WebRTC connection...")
                        
                        # Store connection info in session state for WebRTC handler
                        st.session_state.webrtc_room_url = room_url
                        st.session_state.webrtc_access_token = access_token
                        
                        # For now, show a placeholder
                        self._render_placeholder()
                        st.warning("WebRTC connection requires additional setup. Avatar stream will appear here.")
                else:
                    st.info("👋 Start a session to connect with the avatar")
                    self._render_placeholder()
        
        with col2:
            self._render_controls(session_data)
    
    def _render_placeholder(self) -> None:
        """Render avatar placeholder when not connected."""
        st.markdown(
            """
            <div style="
                width: 100%;
                height: 400px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 24px;
                margin: 20px 0;
            ">
                🤖 Avatar will appear here
            </div>
            """,
            unsafe_allow_html=True
        )
    
    def _render_controls(self, session_data: Optional[Dict[str, Any]]) -> None:
        """Render avatar control panel."""
        st.subheader("Controls")
        
        # Connection status indicator
        status_color = {
            "connected": "🟢",
            "connecting": "🟡",
            "disconnected": "🔴"
        }.get(self.connection_status, "🔴")
        
        st.markdown(f"**Status:** {status_color} {self.connection_status.title()}")
        
        # Quality selector
        quality = st.selectbox(
            "Video Quality",
            ["high", "medium", "low"],
            index=0,
            key="avatar_quality"
        )
        
        # Voice emotion selector
        emotion = st.selectbox(
            "Voice Emotion",
            ["excited", "serious", "friendly", "calm"],
            index=0,
            key="voice_emotion"
        )
        
        # Speaking rate slider
        rate = st.slider(
            "Speaking Rate",
            min_value=0.5,
            max_value=2.0,
            value=1.0,
            step=0.1,
            key="speaking_rate"
        )
        
        # Session info
        if session_data:
            st.markdown("---")
            st.markdown("**Session Info**")
            st.text(f"ID: {session_data.get('session_id', 'N/A')[:12]}...")
            st.text(f"Created: {session_data.get('created_at', 'N/A')}")
            
            # Debug info - show what data we have
            with st.expander("Debug Info"):
                st.json({
                    "has_url": bool(session_data.get("url")),
                    "has_access_token": bool(session_data.get("access_token")),
                    "has_realtime_endpoint": bool(session_data.get("realtime_endpoint")),
                    "url": session_data.get("url", "N/A")[:50] + "..." if session_data.get("url") else "N/A",
                    "session_id": session_data.get("session_id", "N/A")
                })
    
    def _process_audio_frame(self, frame):
        """Process incoming audio frames from avatar."""
        # Add audio processing logic here
        logger.debug("Processing audio frame", size=len(frame.to_ndarray()) if hasattr(frame, 'to_ndarray') else 0)
        return frame
    
    def _process_video_frame(self, frame):
        """Process incoming video frames from avatar."""
        # Add video processing logic here
        logger.debug("Processing video frame")
        return frame
    
    def get_webrtc_context(self):
        """Get the WebRTC context for external access."""
        return self.webrtc_ctx
    
    def is_connected(self) -> bool:
        """Check if avatar is connected."""
        return self.connection_status == "connected"

# Global avatar display instance
avatar_display = AvatarDisplay()
