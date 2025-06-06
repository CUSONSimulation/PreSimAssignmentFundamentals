"""Main Streamlit application for HeyGen Interactive Avatar - FIXED."""

import asyncio
import datetime
from typing import Optional
import streamlit as st
import structlog

# Configure page
st.set_page_config(
    page_title="HeyGen Interactive Avatar",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import components after page config
from config.settings import settings
from core.heygen_client import HeyGenClient
from core.session_manager import session_manager
from components.avatar_display import avatar_display
from components.chat_interface import chat_interface
from utils.logging_config import setup_logging, get_logger, metrics
from utils.error_handlers import HeyGenAPIError, SessionLimitError

# Setup logging
setup_logging(settings.log_level)
logger = get_logger(__name__)

class AvatarApp:
    """Main application class for HeyGen Avatar integration."""
    
    def __init__(self):
        self.heygen_client: Optional[HeyGenClient] = None
        self.current_session_id: Optional[str] = None
        
        # Initialize session state
        self._initialize_session_state()
    
    def _initialize_session_state(self) -> None:
        """Initialize Streamlit session state variables."""
        if "session_active" not in st.session_state:
            st.session_state.session_active = False
        
        if "session_data" not in st.session_state:
            st.session_state.session_data = {}
        
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        
        if "user_id" not in st.session_state:
            st.session_state.user_id = f"user_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if "error_message" not in st.session_state:
            st.session_state.error_message = None
    
    async def start_avatar_session(self) -> bool:
        """Start a new avatar session."""
        try:
            # Check if user can create new session
            if not await session_manager.can_create_session(st.session_state.user_id):
                st.error("Maximum concurrent sessions reached. Please wait for an existing session to end.")
                return False
            
            # Initialize HeyGen client
            self.heygen_client = HeyGenClient()
            
            async with self.heygen_client:
                # Create and start session
                session_data = await self.heygen_client.create_session(
                    quality=st.session_state.get("avatar_quality", "high")
                )
                
                start_data = await self.heygen_client.start_session()
                
                # FIXED: Handle potential None values
                # Store session data
                session_info = {
                    "created_at": datetime.datetime.now().isoformat(),
                    "quality": st.session_state.get("avatar_quality", "high")
                }
                
                # Safely merge session_data if it exists
                if session_data:
                    session_info.update(session_data)
                
                # Safely merge start_data if it exists
                if start_data:
                    session_info.update(start_data)
                
                # Create session in session manager
                self.current_session_id = await session_manager.create_session(
                    st.session_state.user_id,
                    session_info
                )
                
                # Update session state
                st.session_state.session_active = True
                st.session_state.session_data = session_info
                st.session_state.error_message = None
                
                logger.info("Avatar session started successfully", session_id=self.current_session_id)
                return True
                
        except SessionLimitError as e:
            st.error("Session limit reached. Please try again later.")
            logger.warning("Session limit reached", error=str(e))
            
        except HeyGenAPIError as e:
            st.error(f"API Error: {e.message}")
            logger.error("HeyGen API error", error=str(e))
            
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            logger.error("Unexpected error starting session", error=str(e), exc_info=True)
        
        return False
    
    async def stop_avatar_session(self) -> None:
        """Stop the current avatar session."""
        try:
            if self.heygen_client:
                async with self.heygen_client:
                    await self.heygen_client.stop_session()
            
            if self.current_session_id:
                await session_manager.delete_session(self.current_session_id)
            
            # Reset session state
            st.session_state.session_active = False
            st.session_state.session_data = {}
            self.current_session_id = None
            
            logger.info("Avatar session stopped")
            st.success("Session ended successfully")
            
        except Exception as e:
            logger.error("Error stopping session", error=str(e))
            st.warning(f"Error stopping session: {str(e)}")
    
    async def send_message_to_avatar(self, message: str, message_type: str = "text") -> None:
        """Send a message to the avatar."""
        try:
            if not self.heygen_client or not st.session_state.session_active:
                st.error("No active session. Please start a session first.")
                return
            
            async with self.heygen_client:
                success = await self.heygen_client.send_task(message, "talk")
                
                if success:
                    # Add avatar response to chat
                    chat_interface.add_message("assistant", "Message received and processing...")
                    logger.info("Message sent to avatar", message_length=len(message))
                else:
                    st.error("Failed to send message to avatar")
                    
        except Exception as e:
            st.error(f"Error sending message: {str(e)}")
            logger.error("Error sending message to avatar", error=str(e))
    
    def render_header(self) -> None:
        """Render the application header."""
        st.title("🤖 HeyGen Interactive Avatar")
        st.markdown("Real-time AI avatar interactions for nursing education")
        
        # Status bar
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status = "🟢 Active" if st.session_state.session_active else "🔴 Inactive"
            st.metric("Session Status", status)
        
        with col2:
            session_count = len(st.session_state.chat_history)
            st.metric("Messages", session_count)
        
        with col3:
            quality = st.session_state.session_data.get("quality", "N/A")
            st.metric("Video Quality", quality.title())
        
        with col4:
            user_id = st.session_state.user_id[-8:]  # Last 8 chars
            st.metric("User ID", user_id)
    
    def render_sidebar(self) -> None:
        """Render the application sidebar."""
        with st.sidebar:
            st.header("🎛️ Controls")
            
            # Session controls
            st.subheader("Session Management")
            
            if not st.session_state.session_active:
                if st.button("🚀 Start Avatar Session", type="primary", use_container_width=True):
                    # Use asyncio properly for Streamlit
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    success = loop.run_until_complete(self.start_avatar_session())
                    if success:
                        st.rerun()
            else:
                if st.button("⏹️ Stop Session", type="secondary", use_container_width=True):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.stop_avatar_session())
                    st.rerun()
            
            st.divider()
            
            # Settings
            st.subheader("⚙️ Settings")
            
            # Avatar quality
            quality = st.selectbox(
                "Video Quality",
                ["high", "medium", "low"],
                index=0,
                key="avatar_quality_sidebar"
            )
            
            # Voice settings
            emotion = st.selectbox(
                "Voice Emotion",
                ["excited", "serious", "friendly", "calm"],
                index=0,
                key="voice_emotion_sidebar"
            )
            
            rate = st.slider(
                "Speaking Rate",
                min_value=0.5,
                max_value=2.0,
                value=1.0,
                step=0.1,
                key="speaking_rate_sidebar"
            )
            
            st.divider()
            
            # Metrics
            st.subheader("📊 Metrics")
            app_metrics = metrics.get_metrics()
            
            for metric_name, value in app_metrics.items():
                st.text(f"{metric_name}: {value}")
            
            st.divider()
            
            # Debug info
            with st.expander("🔍 Debug Info"):
                debug_info = {
                    "session_active": st.session_state.session_active,
                    "user_id": st.session_state.user_id,
                    "session_data_keys": list(st.session_state.session_data.keys()) if st.session_state.session_data else [],
                    "chat_history_length": len(st.session_state.chat_history)
                }
                st.json(debug_info)
    
    def render_main_content(self) -> None:
        """Render the main application content."""
        
        # Create main layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Avatar display
            avatar_display.render(st.session_state.session_data)
        
        with col2:
            # Chat interface
            # FIXED: Properly handle async message sending
            def handle_message_send(msg: str, msg_type: str):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.send_message_to_avatar(msg, msg_type))
            
            chat_interface.render(on_message_send=handle_message_send)
        
        # Error handling
        if st.session_state.error_message:
            st.error(st.session_state.error_message)
            st.session_state.error_message = None
    
    def run(self) -> None:
        """Run the main application."""
        try:
            # Load chat history if exists
            if st.session_state.chat_history:
                chat_interface.load_chat_history(st.session_state.chat_history)
            
            # Render application
            self.render_header()
            self.render_sidebar()
            self.render_main_content()
            
            # Cleanup expired sessions periodically
            if st.session_state.session_active:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(session_manager.cleanup_expired_sessions())
                
        except Exception as e:
            st.error(f"Application error: {str(e)}")
            logger.error("Application error", error=str(e), exc_info=True)

def main():
    """Application entry point."""
    app = AvatarApp()
    app.run()

if __name__ == "__main__":
    main()
