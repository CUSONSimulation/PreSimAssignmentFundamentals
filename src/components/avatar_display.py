"""Avatar display component with video streaming - SIMPLIFIED FOR HEYGEN V2."""

import streamlit as st
import streamlit.components.v1 as components
from typing import Optional, Dict, Any
import structlog
import json
import base64

logger = structlog.get_logger(__name__)

class AvatarDisplay:
    """Component for displaying the avatar video stream."""
    
    def __init__(self):
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
                if session_data and session_data.get("url") and session_data.get("access_token"):
                    # Log connection details
                    logger.info("Avatar session data available", 
                              session_id=session_data.get("session_id"),
                              has_url=bool(session_data.get("url")),
                              has_token=bool(session_data.get("access_token")))
                    
                    # For HeyGen v2, we need to create a custom component
                    # that handles the WebRTC connection
                    self._render_heygen_avatar(session_data)
                    
                else:
                    st.info("👋 Start a session to connect with the avatar")
                    self._render_placeholder()
        
        with col2:
            self._render_controls(session_data)
    
    def _render_heygen_avatar(self, session_data: Dict[str, Any]) -> None:
        """Render the HeyGen avatar using custom HTML/JS."""
        
        # Create the WebRTC connection HTML
        avatar_html = f"""
        <div id="avatar-container" style="width: 100%; height: 500px; background: #000; border-radius: 10px; position: relative;">
            <video id="avatarVideo" autoplay playsinline style="width: 100%; height: 100%; object-fit: cover;"></video>
            <div id="status" style="position: absolute; top: 10px; left: 10px; color: white; background: rgba(0,0,0,0.7); padding: 5px 10px; border-radius: 5px;">
                Connecting to avatar...
            </div>
        </div>
        
        <script>
            // HeyGen Interactive Avatar v2 Connection
            const sessionData = {json.dumps({
                'url': session_data.get('url'),
                'token': session_data.get('access_token'),
                'sessionId': session_data.get('session_id'),
                'realtimeEndpoint': session_data.get('realtime_endpoint')
            })};
            
            console.log('Session data:', sessionData);
            
            // For now, we'll display a message about the connection
            // Full WebRTC implementation requires more complex setup
            
            const statusEl = document.getElementById('status');
            const videoEl = document.getElementById('avatarVideo');
            
            // Update status
            statusEl.innerHTML = `
                <div>✅ Session Active</div>
                <div style="font-size: 12px; margin-top: 5px;">
                    Session ID: ${{sessionData.sessionId.substring(0, 12)}}...
                </div>
            `;
            
            // Note: Full WebRTC implementation would go here
            // For now, showing session is active
            
            // You can implement the full WebRTC connection here if needed
            // This would involve:
            // 1. Creating RTCPeerConnection
            // 2. Connecting to the WebSocket endpoint
            // 3. Handling offer/answer exchange
            // 4. Displaying the remote video stream
            
        </script>
        """
        
        # Display the HTML component
        components.html(avatar_html, height=520)
        
        # Show connection info
        with st.expander("🔧 Connection Details"):
            st.info("""
            **Avatar Session is Active!**
            
            The avatar is ready to receive messages. Due to WebRTC complexity in Streamlit, 
            the video stream may not display properly in this interface.
            
            For full video streaming, you may need to:
            1. Use the HeyGen SDK directly
            2. Implement a custom WebRTC component
            3. Use HeyGen's preview interface
            """)
            
            # Show session details
            st.json({
                "session_id": session_data.get("session_id"),
                "websocket_url": session_data.get("url", "")[:50] + "...",
                "has_access_token": bool(session_data.get("access_token")),
                "realtime_endpoint": session_data.get("realtime_endpoint", "")[:50] + "..."
            })
    
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
        if session_data and session_data.get("session_id"):
            st.markdown("**Status:** 🟢 Connected")
            self.connection_status = "connected"
        else:
            st.markdown("**Status:** 🔴 Disconnected")
            self.connection_status = "disconnected"
        
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
            
            # Safely display session ID
            session_id = session_data.get("session_id", "N/A")
            if session_id != "N/A" and len(session_id) > 12:
                display_id = f"{session_id[:12]}..."
            else:
                display_id = session_id
            
            st.text(f"ID: {display_id}")
            st.text(f"Created: {session_data.get('created_at', 'N/A')[:19] if session_data.get('created_at') else 'N/A'}")

# Global avatar display instance
avatar_display = AvatarDisplay()
