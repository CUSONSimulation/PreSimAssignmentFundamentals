import streamlit as st
import requests
import json
import time
import os
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HeyGenAvatarSession:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.heygen.com/v1"
        self.session_id = None
        self.session_token = None
        
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make HTTP request to HeyGen API with proper error handling"""
        url = f"{self.base_url}/{endpoint}"
        headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            logger.info(f"Making {method} request to {endpoint}")
            if data:
                logger.debug(f"Request payload: {json.dumps(data, indent=2)}")
            
            if method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                response = requests.get(url, headers=headers, timeout=30)
            
            logger.info(f"Response status: {response.status_code}")
            response.raise_for_status()
            
            result = response.json()
            logger.debug(f"Response data: {json.dumps(result, indent=2)}")
            return result
            
        except requests.RequestException as e:
            logger.error(f"API Request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    logger.error(f"Error details: {error_detail}")
                    st.error(f"API Error: {error_detail}")
                except:
                    logger.error(f"Response text: {e.response.text}")
                    st.error(f"API Error: {e.response.text}")
            raise

    def get_valid_voices(self) -> list:
        """Get list of voices that support interactive avatars"""
        try:
            # Use v2 endpoint for better voice data
            url = "https://api.heygen.com/v2/voices"
            headers = {
                "X-Api-Key": self.api_key,
                "Accept": "application/json"
            }
            
            logger.info("Fetching available voices...")
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            voices = data.get("data", {}).get("voices", [])
            
            # Filter for streaming-compatible voices
            streaming_voices = [
                voice for voice in voices 
                if voice.get("support_interactive_avatar", False)
            ]
            
            logger.info(f"Found {len(streaming_voices)} streaming-compatible voices")
            return streaming_voices
            
        except Exception as e:
            logger.error(f"Failed to fetch voices: {e}")
            st.error(f"Failed to fetch voices: {e}")
            return []

    def create_session_token(self) -> str:
        """Generate session token"""
        try:
            logger.info("Creating session token...")
            response = self._make_request("POST", "streaming.create_token")
            token = response.get("data", {}).get("token")
            
            if not token:
                raise ValueError("No token received from API")
                
            self.session_token = token
            logger.info("Session token created successfully")
            return token
            
        except Exception as e:
            logger.error(f"Failed to create session token: {e}")
            st.error(f"Failed to create session token: {e}")
            raise

    def create_streaming_session(
        self, 
        avatar_id: str, 
        voice_id: str, 
        knowledge_id: Optional[str] = None,
        quality: str = "high"
    ) -> Dict:
        """Create new streaming session with valid voice ID"""
        
        if not self.session_token:
            self.create_session_token()
        
        payload = {
            "version": "v2",
            "avatar_id": avatar_id,
            "quality": quality,
            "voice": {
                "voice_id": voice_id,
                "rate": 1.0,
                "emotion": "excited"
            }
        }
        
        # Add knowledge base if provided
        if knowledge_id:
            payload["knowledge_id"] = knowledge_id
            
        try:
            logger.info(f"Creating streaming session with avatar: {avatar_id}, voice: {voice_id}")
            response = self._make_request("POST", "streaming.new", payload)
            
            session_data = response.get("data", {})
            self.session_id = session_data.get("session_id")
            
            if not self.session_id:
                raise ValueError("No session ID received")
            
            logger.info(f"Streaming session created successfully: {self.session_id}")
            return session_data
            
        except Exception as e:
            logger.error(f"Failed to create streaming session: {e}")
            st.error(f"Failed to create streaming session: {e}")
            raise

    def send_message(self, text: str) -> Dict:
        """Send text message to avatar"""
        if not self.session_id:
            raise ValueError("No active session")
            
        payload = {
            "session_id": self.session_id,
            "text": text,
            "task_type": "talk"
        }
        
        logger.info(f"Sending message to avatar: {text[:50]}...")
        return self._make_request("POST", "streaming.task", payload)

    def close_session(self) -> Dict:
        """Close the streaming session"""
        if not self.session_id:
            return {"message": "No session to close"}
            
        payload = {"session_id": self.session_id}
        logger.info(f"Closing session: {self.session_id}")
        response = self._make_request("POST", "streaming.stop", payload)
        
        self.session_id = None
        self.session_token = None
        
        return response

    def list_active_sessions(self) -> Dict:
        """List all active sessions"""
        try:
            return self._make_request("GET", "streaming.list")
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return {"data": []}

def cleanup_on_startup():
    """Clean up any existing sessions on app startup"""
    if 'heygen_session' in st.session_state:
        try:
            if st.session_state.heygen_session and st.session_state.session_active:
                st.session_state.heygen_session.close_session()
        except:
            pass
        st.session_state.session_active = False

def main():
    st.set_page_config(
        page_title="Pre-Sim Assignment Fundamentals",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Clean up on startup
    cleanup_on_startup()
    
    st.title("🏥 HeyGen Interactive Avatar - Pre-Sim Assignment Fundamentals")
    st.markdown("---")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key input - try to get from secrets first
        default_api_key = ""
        try:
            default_api_key = st.secrets.get("heygen", {}).get("api_key", "")
        except:
            pass
        
        api_key = st.text_input(
            "HeyGen API Key", 
            value=default_api_key,
            type="password",
            help="Enter your HeyGen API key"
        )
        
        # Avatar ID input
        avatar_id = st.text_input(
            "Avatar ID", 
            value="Rika_Chair_Sitting_public",
            help="Enter the avatar ID to use"
        )
        
        # Knowledge ID input
        knowledge_id = st.text_input(
            "Knowledge ID (Optional)", 
            value="6bbcea1ca7ab4640a7802da4d1492e62",
            help="Enter the knowledge base ID (leave empty if not using)"
        )
        
        # Quality setting
        quality = st.selectbox(
            "Video Quality",
            options=["high", "medium", "low"],
            index=0,
            help="Higher quality uses more bandwidth"
        )
        
        st.markdown("---")
        
        # Get valid voices
        if api_key:
            with st.spinner("🔍 Fetching available voices..."):
                try:
                    heygen = HeyGenAvatarSession(api_key)
                    voices = heygen.get_valid_voices()
                except Exception as e:
                    st.error(f"Failed to connect to HeyGen API: {e}")
                    voices = []
                
            if voices:
                st.success(f"✅ Found {len(voices)} compatible voices")
                
                # Voice selection dropdown
                voice_options = {}
                for voice in voices[:30]:  # Limit to first 30 for performance
                    display_name = f"{voice['name']} ({voice['gender']}, {voice['language']})"
                    voice_options[display_name] = voice['voice_id']
                
                if voice_options:
                    selected_voice_display = st.selectbox(
                        "Select Voice",
                        options=list(voice_options.keys()),
                        help="Choose a voice that supports interactive avatars"
                    )
                    
                    selected_voice_id = voice_options[selected_voice_display]
                    st.info(f"**Selected Voice ID:** `{selected_voice_id}`")
                else:
                    st.error("❌ No voices available for selection")
                    selected_voice_id = None
                
                # Show session info
                if st.button("📊 Check Active Sessions"):
                    try:
                        sessions = heygen.list_active_sessions()
                        active_sessions = sessions.get("data", [])
                        st.json({
                            "active_sessions": len(active_sessions),
                            "sessions": active_sessions
                        })
                    except Exception as e:
                        st.error(f"Failed to check sessions: {e}")
                        
            else:
                st.error("❌ No compatible voices found. Please check your API key and try again.")
                selected_voice_id = None
        else:
            st.warning("👆 Please enter your HeyGen API key to continue")
            selected_voice_id = None

    # Main content area
    if api_key and selected_voice_id:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.header("🎭 Avatar Interaction")
            
            # Session management
            if 'heygen_session' not in st.session_state:
                st.session_state.heygen_session = None
                st.session_state.session_active = False
            
            # Start session button
            if not st.session_state.session_active:
                if st.button("🚀 Start Avatar Session", type="primary", use_container_width=True):
                    try:
                        with st.spinner("Creating avatar session... This may take a few moments."):
                            heygen = HeyGenAvatarSession(api_key)
                            
                            # Clean knowledge_id if empty
                            clean_knowledge_id = knowledge_id.strip() if knowledge_id and knowledge_id.strip() else None
                            
                            session_data = heygen.create_streaming_session(
                                avatar_id=avatar_id,
                                voice_id=selected_voice_id,
                                knowledge_id=clean_knowledge_id,
                                quality=quality
                            )
                            
                        st.session_state.heygen_session = heygen
                        st.session_state.session_active = True
                        st.session_state.session_data = session_data
                        
                        st.success("✅ Avatar session created successfully!")
                        with st.expander("📋 Session Details", expanded=False):
                            st.json(session_data)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Failed to create session: {e}")
                        st.info("💡 **Troubleshooting tips:**")
                        st.info("- Check if you have reached your concurrent session limit (3 sessions)")
                        st.info("- Verify your API key has streaming avatar permissions")
                        st.info("- Try a different voice ID")
            
            else:
                st.success("✅ Avatar session is active!")
                
                # Message input
                st.subheader("💬 Chat with Avatar")
                user_message = st.text_area(
                    "Enter your message:",
                    placeholder="Type your message here...",
                    height=100
                )
                
                col_send, col_stop = st.columns(2)
                
                with col_send:
                    if st.button("📤 Send Message", type="primary", disabled=not user_message.strip()):
                        if user_message.strip():
                            try:
                                with st.spinner("Sending message to avatar..."):
                                    response = st.session_state.heygen_session.send_message(user_message.strip())
                                st.success("✅ Message sent successfully!")
                                with st.expander("📋 Response Details", expanded=False):
                                    st.json(response)
                            except Exception as e:
                                st.error(f"❌ Failed to send message: {e}")
                
                with col_stop:
                    if st.button("🛑 Stop Session", type="secondary"):
                        try:
                            with st.spinner("Closing session..."):
                                if st.session_state.heygen_session:
                                    response = st.session_state.heygen_session.close_session()
                            
                            st.session_state.session_active = False
                            st.session_state.heygen_session = None
                            
                            st.success("✅ Session closed successfully!")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Failed to close session: {e}")
        
        with col2:
            st.header("📊 Session Info")
            
            if st.session_state.session_active and 'session_data' in st.session_state:
                session_info = {
                    "🟢 Status": "Active",
                    "🆔 Session ID": st.session_state.session_data.get("session_id", "N/A")[:20] + "...",
                    "🎭 Avatar": avatar_id,
                    "🗣️ Voice": selected_voice_id[:20] + "...",
                    "🧠 Knowledge Base": knowledge_id[:20] + "..." if knowledge_id else "None",
                    "📺 Quality": quality.title()
                }
                
                for key, value in session_info.items():
                    st.metric(key, value)
                    
                # Show full session data in expander
                with st.expander("🔍 Full Session Data"):
                    st.json(st.session_state.session_data)
                    
            else:
                st.info("🔴 No active session")
                st.json({
                    "session_active": False,
                    "session_id": None,
                    "avatar_id": avatar_id,
                    "voice_id": selected_voice_id[:20] + "..." if selected_voice_id else None
                })
    
    else:
        # Welcome screen
        st.markdown("""
        ## 👋 Welcome to the Pre-Sim Assignment Fundamentals
        
        This interactive avatar will help guide you through your pre-simulation assignments.
        
        ### 🚀 Getting Started:
        1. **Enter your HeyGen API key** in the sidebar
        2. **Select a voice** for your avatar
        3. **Configure settings** (optional)
        4. **Start your session** and begin interacting!
        
        ### 🔧 Configuration Tips:
        - Use the default avatar and knowledge base for nursing simulations
        - Choose a voice that matches your preference
        - Higher quality settings require more bandwidth
        
        ### 🆘 Need Help?
        - Check the troubleshooting guide in the repository
        - Verify your API key has streaming avatar permissions
        - Ensure you haven't exceeded the 3 concurrent session limit
        """)
        
        st.info("👈 **Please configure your settings in the sidebar to get started**")

    # Footer
    st.markdown("---")
    st.markdown(
        "Built with ❤️ using [Streamlit](https://streamlit.io) and [HeyGen](https://heygen.com) | "
        "[GitHub Repository](https://github.com/CUSONSimulation/PreSimAssignmentFundamentals)"
    )

if __name__ == "__main__":
    main()
