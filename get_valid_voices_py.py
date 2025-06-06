#!/usr/bin/env python3
"""
HeyGen Voice ID Fetcher
Utility script to fetch and display valid voice IDs for streaming avatars
"""

import requests
import json
import sys
import os
from typing import List, Dict

def get_streaming_compatible_voices(api_key: str) -> List[Dict]:
    """
    Fetch all voices that support interactive avatars from HeyGen API v2
    """
    url = "https://api.heygen.com/v2/voices"
    
    headers = {
        "X-Api-Key": api_key,
        "Accept": "application/json"
    }
    
    try:
        print("🔍 Fetching voices from HeyGen API...")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        voices = data.get("data", {}).get("voices", [])
        
        # Filter voices that support interactive avatars
        streaming_voices = [
            voice for voice in voices 
            if voice.get("support_interactive_avatar", False)
        ]
        
        print(f"✅ Successfully fetched {len(voices)} total voices")
        print(f"🎯 Found {len(streaming_voices)} voices compatible with streaming avatars\n")
        
        return streaming_voices
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching voices: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"   Error details: {error_detail}")
            except:
                print(f"   Response text: {e.response.text}")
        return []
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return []

def display_voices(voices: List[Dict], limit: int = 20):
    """Display voices in a formatted way"""
    if not voices:
        print("❌ No streaming-compatible voices found!")
        return
    
    print("🎤 STREAMING-COMPATIBLE VOICES:")
    print("=" * 80)
    
    for i, voice in enumerate(voices[:limit], 1):
        print(f"{i:2d}. 🎵 {voice['name']}")
        print(f"    📋 Voice ID: {voice['voice_id']}")
        print(f"    🌍 Language: {voice['language']}")
        print(f"    👤 Gender: {voice['gender']}")
        print(f"    😊 Emotion Support: {'✅' if voice.get('emotion_support', False) else '❌'}")
        print(f"    ⏸️  Pause Support: {'✅' if voice.get('support_pause', False) else '❌'}")
        
        # Preview audio if available
        if voice.get('preview_audio'):
            print(f"    🔊 Preview: {voice['preview_audio']}")
        
        print("-" * 60)
    
    if len(voices) > limit:
        print(f"\n... and {len(voices) - limit} more voices available.")

def save_voices_to_file(voices: List[Dict], filename: str = "valid_voice_ids.json"):
    """Save voices to a JSON file"""
    try:
        with open(filename, 'w') as f:
            json.dump(voices, f, indent=2)
        print(f"💾 Voice data saved to {filename}")
    except Exception as e:
        print(f"❌ Failed to save to file: {e}")

def get_recommended_voice(voices: List[Dict]) -> Dict:
    """Get a recommended voice for testing"""
    if not voices:
        return None
    
    # Prefer English voices with emotion support
    english_voices = [v for v in voices if 'english' in v.get('language', '').lower()]
    emotion_voices = [v for v in english_voices if v.get('emotion_support', False)]
    
    if emotion_voices:
        return emotion_voices[0]
    elif english_voices:
        return english_voices[0]
    else:
        return voices[0]

def main():
    print("🎤 HeyGen Voice ID Fetcher")
    print("=" * 50)
    
    # Get API key from command line, environment, or user input
    api_key = None
    
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    elif os.getenv('HEYGEN_API_KEY'):
        api_key = os.getenv('HEYGEN_API_KEY')
        print("🔑 Using API key from environment variable")
    else:
        api_key = input("🔑 Enter your HeyGen API key: ").strip()
    
    if not api_key:
        print("❌ No API key provided!")
        print("\nUsage:")
        print("  python get_valid_voices.py YOUR_API_KEY")
        print("  OR set HEYGEN_API_KEY environment variable")
        print("  OR run without arguments and enter key when prompted")
        sys.exit(1)
    
    # Fetch voices
    voices = get_streaming_compatible_voices(api_key)
    
    if not voices:
        print("\n💡 Troubleshooting:")
        print("   - Check your API key is valid")
        print("   - Ensure your account has streaming avatar access")
        print("   - Verify your internet connection")
        sys.exit(1)
    
    # Display voices
    display_voices(voices)
    
    # Show recommended voice
    recommended = get_recommended_voice(voices)
    if recommended:
        print("\n🎯 RECOMMENDED VOICE FOR TESTING:")
        print("=" * 50)
        print(f"Voice ID: {recommended['voice_id']}")
        print(f"Name: {recommended['name']}")
        print(f"Language: {recommended['language']}")
        print(f"Gender: {recommended['gender']}")
        print("\n📋 Copy this voice ID to use in your Streamlit app!")
    
    # Save to file
    save_voices_to_file(voices)
    
    # Show usage example
    print(f"\n🔧 USAGE EXAMPLE:")
    print("=" * 50)
    print("Replace 'claire' in your code with one of these valid voice IDs:")
    print(f"""
# In your streaming session payload:
"voice": {{
    "voice_id": "{recommended['voice_id'] if recommended else 'VOICE_ID_HERE'}",
    "rate": 1.0,
    "emotion": "excited"
}}
""")

if __name__ == "__main__":
    main()
