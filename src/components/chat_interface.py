"""Chat interface component for text and voice interactions."""

import streamlit as st
import asyncio
import datetime
import json
from typing import List, Dict, Any, Optional
import structlog
from utils.logging_config import metrics

logger = structlog.get_logger(__name__)

class ChatInterface:
    """Component for chat interactions with the avatar."""
    
    def __init__(self):
        self.chat_history: List[Dict[str, str]] = []
        self.voice_recording = False
    
    def render(self, on_message_send: Optional[callable] = None) -> None:
        """Render the chat interface."""
        
        st.subheader("💬 Chat with Avatar")
        
        # Chat history container
        chat_container = st.container()
        
        with chat_container:
            self._render_chat_history()
        
        # Input section
        self._render_input_section(on_message_send)
        
        # Controls
        self._render_chat_controls()
    
    def _render_chat_history(self) -> None:
        """Render the chat message history."""
        if not self.chat_history:
            st.info("👋 Start a conversation with the avatar!")
            return
        
        # Create scrollable chat container
        with st.container():
            for i, message in enumerate(self.chat_history[-10:]):  # Show last 10 messages
                self._render_message(message, i)
    
    def _render_message(self, message: Dict[str, str], index: int) -> None:
        """Render a single chat message."""
        role = message.get("role", "user")
        content = message.get("content", "")
        timestamp = message.get("timestamp", "")
        
        if role == "user":
            # User message (right aligned)
            st.markdown(
                f"""
                <div style="
                    display: flex;
                    justify-content: flex-end;
                    margin: 10px 0;
                ">
                    <div style="
                        background-color: #007bff;
                        color: white;
                        padding: 10px 15px;
                        border-radius: 18px 18px 5px 18px;
                        max-width: 70%;
                        word-wrap: break-word;
                    ">
                        {content}
                        <div style="font-size: 10px; opacity: 0.7; margin-top: 5px;">
                            {timestamp}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            # Avatar message (left aligned)
            st.markdown(
                f"""
                <div style="
                    display: flex;
                    justify-content: flex-start;
                    margin: 10px 0;
                ">
                    <div style="
                        background-color: #f1f3f4;
                        color: #333;
                        padding: 10px 15px;
                        border-radius: 18px 18px 18px 5px;
                        max-width: 70%;
                        word-wrap: break-word;
                    ">
                        🤖 {content}
                        <div style="font-size: 10px; opacity: 0.7; margin-top: 5px;">
                            {timestamp}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    def _render_input_section(self, on_message_send: Optional[callable]) -> None:
        """Render the message input section."""
        
        # Create columns for input and buttons
        col1, col2, col3 = st.columns([6, 1, 1])
        
        with col1:
            # Text input
            message_text = st.text_input(
                "Type your message...",
                key="chat_input",
                placeholder="Ask the avatar anything...",
                label_visibility="collapsed"
            )
        
        with col2:
            # Send button
            send_clicked = st.button("📤", key="send_button", help="Send message")
        
        with col3:
            # Voice button
            if not self.voice_recording:
                voice_clicked = st.button("🎤", key="voice_button", help="Record voice message")
            else:
                st.button("⏹️", key="stop_voice_button", help="Stop recording")
                voice_clicked = False
        
        # Handle message sending
        if (send_clicked or st.session_state.get("chat_input_submitted")) and message_text.strip():
            if on_message_send:
                asyncio.create_task(on_message_send(message_text.strip(), "text"))
            
            self.add_message("user", message_text.strip())
            st.session_state.chat_input = ""  # Clear input
            st.rerun()
        
        # Handle voice recording
        if voice_clicked:
            self._toggle_voice_recording()
    
    def _render_chat_controls(self) -> None:
        """Render chat control buttons."""
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🗑️ Clear Chat", key="clear_chat"):
                self.clear_chat()
                st.rerun()
        
        with col2:
            if st.button("💾 Save Chat", key="save_chat"):
                self._save_chat_history()
        
        with col3:
            if st.button("📋 Export", key="export_chat"):
                self._export_chat_history()
    
    def add_message(self, role: str, content: str, timestamp: Optional[str] = None) -> None:
        """Add a message to the chat history."""
        
        if not timestamp:
            timestamp = datetime.datetime.now().strftime("%H:%M")
        
        message = {
            "role": role,
            "content": content,
            "timestamp": timestamp
        }
        
        self.chat_history.append(message)
        
        # Update session state
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        st.session_state.chat_history = self.chat_history
        
        logger.info("Message added to chat", role=role, content_length=len(content))
        metrics.increment(f"messages_{role}")
    
    def clear_chat(self) -> None:
        """Clear the chat history."""
        self.chat_history = []
        if "chat_history" in st.session_state:
            st.session_state.chat_history = []
        
        logger.info("Chat history cleared")
        metrics.increment("chat_cleared")
    
    def _toggle_voice_recording(self) -> None:
        """Toggle voice recording state."""
        self.voice_recording = not self.voice_recording
        
        if self.voice_recording:
            st.info("🎤 Recording voice message... Click stop when done.")
            logger.info("Voice recording started")
            metrics.increment("voice_recordings_started")
        else:
            st.success("Voice message recorded!")
            logger.info("Voice recording stopped")
            metrics.increment("voice_recordings_completed")
    
    def _save_chat_history(self) -> None:
        """Save chat history to session state."""
        if "saved_chats" not in st.session_state:
            st.session_state.saved_chats = []
        
        saved_chat = {
            "timestamp": datetime.datetime.now().isoformat(),
            "messages": self.chat_history.copy()
        }
        
        st.session_state.saved_chats.append(saved_chat)
        st.success("Chat saved successfully!")
        
        logger.info("Chat history saved", message_count=len(self.chat_history))
    
    def _export_chat_history(self) -> None:
        """Export chat history as downloadable file."""
        
        export_data = {
            "chat_history": self.chat_history,
            "exported_at": datetime.datetime.now().isoformat(),
            "message_count": len(self.chat_history)
        }
        
        st.download_button(
            label="📥 Download Chat",
            data=json.dumps(export_data, indent=2),
            file_name=f"avatar_chat_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    def get_chat_history(self) -> List[Dict[str, str]]:
        """Get the current chat history."""
        return self.chat_history.copy()
    
    def load_chat_history(self, history: List[Dict[str, str]]) -> None:
        """Load chat history from external source."""
        self.chat_history = history.copy()
        st.session_state.chat_history = self.chat_history

# Global chat interface instance
chat_interface = ChatInterface()