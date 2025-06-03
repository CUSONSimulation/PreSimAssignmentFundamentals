"""Avatar display component with video streaming."""

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
                if session_data and session_data.get("room_url"):
                    # Setup WebRTC streamer
                    self.webrtc_ctx = webrtc_handler.setup_webrtc_streamer(
                        key="avatar_stream",
                        on_audio_frame=self._process_audio_frame,
                        on_video_frame=self._process_video_frame
                    )
                    
                    # Display connection status
                    if self.webrtc_ctx.state.playing:
                        st.success("🟢 Connected to avatar")
                        self.connection_status = "connected"
                        metrics.increment("avatar_connections_active")
                    else:
                        st.warning("🟡 Connecting to avatar...")
                        self.connection_status = "connecting"
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
            
            # Connection stats
            stats = webrtc_handler.get_connection_stats()
            if stats:
                st.text(f"WebRTC: {stats.get('connection_state', 'unknown')}")
    
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