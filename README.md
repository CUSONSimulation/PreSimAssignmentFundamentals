# HeyGen Interactive Avatar + Streamlit Integration

A production-ready application that integrates HeyGen's Interactive Avatar API with Streamlit for real-time avatar interactions. Designed for educational purposes, particularly nursing simulations with AI avatars.

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/heygen-streamlit-avatar.git
   cd heygen-streamlit-avatar
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your HeyGen API key
   ```

4. **Run the application**
   ```bash
   streamlit run src/app.py
   ```

## 📋 Prerequisites

- Python 3.9+
- HeyGen API key (get from [HeyGen Console](https://app.heygen.com))
- Redis (optional, for session persistence)

## 🏗️ Architecture

```
Frontend (Streamlit) ↔ WebRTC (LiveKit) ↔ HeyGen Avatar API
                     ↕
              Session Manager ↔ Redis Cache
```

## 🔧 Configuration

### Environment Variables
- `HEYGEN_API_KEY`: Your HeyGen API key
- `KNOWLEDGE_BASE_ID`: Knowledge base for avatar responses
- `AVATAR_ID`: HeyGen avatar identifier
- `REDIS_URL`: Redis connection string (optional)

## 🎯 Features

- Real-time avatar conversations
- Voice and text interactions
- Knowledge base integration
- Session management
- Error recovery
- Credit monitoring

## 📁 Project Structure

```
heygen-streamlit-avatar/
├── README.md
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example
├── src/
│   ├── __init__.py
│   ├── app.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── heygen_client.py
│   │   ├── session_manager.py
│   │   └── webrtc_handler.py
│   ├── components/
│   │   ├── __init__.py
│   │   ├── avatar_display.py
│   │   └── chat_interface.py
│   └── utils/
│       ├── __init__.py
│       ├── error_handlers.py
│       └── logging_config.py
├── tests/
│   ├── __init__.py
│   └── test_heygen_client.py
└── deployment/
    ├── render.yaml
    └── streamlit_cloud.md
```

## 🚀 Deployment

### Streamlit Cloud
1. Connect your GitHub repository
2. Add secrets in Streamlit Cloud dashboard
3. Deploy automatically

### Render.com
```bash
render deploy --service-type web
```

### Docker
```bash
docker-compose up -d
```

## 📊 Monitoring

- Built-in logging with structured output
- Session metrics tracking
- Error rate monitoring
- Credit usage tracking

## ⚙️ Configuration Options

- Video quality settings (high/medium/low)
- Voice emotion control
- Speaking rate adjustment
- Session timeout management
- Concurrent session limits

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📚 Usage Examples

### Basic Session Management
```python
# Start avatar session
await app.start_avatar_session()

# Send message to avatar
await app.send_message_to_avatar("Hello, how can you help with nursing education?")

# Stop session
await app.stop_avatar_session()
```

### Custom Configuration
```python
# Configure avatar settings
settings.avatar_quality = "high"
settings.voice_emotion = "friendly"
settings.speaking_rate = 1.2
```

## 🔒 Security

- API keys stored securely in environment variables
- HTTPS enforcement for all communications
- Session token encryption
- Input validation and sanitization

## 🐛 Troubleshooting

### Common Issues

1. **Session limit reached**: Wait for existing sessions to expire or upgrade your HeyGen plan
2. **WebRTC connection failed**: Check firewall settings and STUN/TURN configuration
3. **Audio not working**: Verify microphone permissions in browser
4. **Avatar not appearing**: Check API key and network connectivity

### Debug Mode
Run with debug logging:
```bash
LOG_LEVEL=DEBUG streamlit run src/app.py
```

## 📝 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- [HeyGen](https://heygen.com) for the Interactive Avatar API
- [Streamlit](https://streamlit.io) for the web framework
- [LiveKit](https://livekit.io) for WebRTC infrastructure