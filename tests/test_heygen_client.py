"""Tests for HeyGen client functionality."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from core.heygen_client import HeyGenClient
from utils.error_handlers import HeyGenAPIError, SessionLimitError

@pytest.fixture
def heygen_client():
    """Create a HeyGen client for testing."""
    return HeyGenClient()

@pytest.mark.asyncio
async def test_generate_session_token_success(heygen_client):
    """Test successful session token generation."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"token": "test_token_123"}
    mock_response.raise_for_status = MagicMock()
    
    with patch.object(heygen_client, '_client') as mock_client:
        mock_client.post = AsyncMock(return_value=mock_response)
        
        token = await heygen_client.generate_session_token()
        
        assert token == "test_token_123"
        assert heygen_client.session_token == "test_token_123"
        mock_client.post.assert_called_once()

@pytest.mark.asyncio
async def test_create_session_success(heygen_client):
    """Test successful session creation."""
    heygen_client.session_token = "test_token"
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"session_id": "session_123"}
    mock_response.raise_for_status = MagicMock()
    
    with patch.object(heygen_client, '_client') as mock_client:
        mock_client.post = AsyncMock(return_value=mock_response)
        
        result = await heygen_client.create_session()
        
        assert result["session_id"] == "session_123"
        assert heygen_client.session_id == "session_123"

@pytest.mark.asyncio
async def test_session_limit_error(heygen_client):
    """Test handling of session limit errors."""
    heygen_client.session_token = "test_token"
    
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"error": "concurrent session limit reached"}
    
    with patch.object(heygen_client, '_client') as mock_client:
        mock_client.post = AsyncMock(return_value=mock_response)
        
        with pytest.raises(SessionLimitError):
            await heygen_client.create_session()

@pytest.mark.asyncio
async def test_send_task_success(heygen_client):
    """Test successful task sending."""
    heygen_client.session_token = "test_token"
    heygen_client.session_id = "session_123"
    heygen_client.session_active = True
    
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    
    with patch.object(heygen_client, '_client') as mock_client:
        mock_client.post = AsyncMock(return_value=mock_response)
        
        result = await heygen_client.send_task("Hello, avatar!")
        
        assert result is True
        mock_client.post.assert_called_once()

def test_client_initialization():
    """Test client initialization with settings."""
    client = HeyGenClient()
    
    assert client.api_key is not None
    assert client.base_url is not None
    assert client.session_token is None
    assert client.session_id is None
    assert client.session_active is False