"""Error handling utilities with circuit breaker pattern."""

import asyncio
import time
from typing import Any, Callable, Optional, Type
from functools import wraps
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx

logger = structlog.get_logger(__name__)

class HeyGenAPIError(Exception):
    """Custom exception for HeyGen API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[dict] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)

class SessionLimitError(HeyGenAPIError):
    """Raised when session limit is exceeded."""
    pass

class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""
    pass

class CircuitBreaker:
    """Circuit breaker for API calls."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker moving to HALF_OPEN")
            else:
                raise CircuitBreakerError("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.reset()
            return result
        except Exception as e:
            self.record_failure()
            raise e
    
    def record_failure(self) -> None:
        """Record a failure and potentially open the circuit."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(
                "Circuit breaker opened",
                failure_count=self.failure_count,
                threshold=self.failure_threshold
            )
    
    def reset(self) -> None:
        """Reset the circuit breaker."""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"
        logger.info("Circuit breaker reset")

# Global circuit breaker instance
api_circuit_breaker = CircuitBreaker()

def handle_api_errors(func: Callable) -> Callable:
    """Decorator for handling API errors with retries."""
    
    @retry(
        retry=retry_if_exception_type((httpx.HTTPError, HeyGenAPIError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await api_circuit_breaker.call(func, *args, **kwargs)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning("Rate limit exceeded", status_code=429)
                raise HeyGenAPIError("Rate limit exceeded", 429)
            elif e.response.status_code == 400:
                error_data = e.response.json() if e.response.headers.get("content-type") == "application/json" else {}
                if "concurrent session limit" in str(error_data).lower():
                    raise SessionLimitError("Concurrent session limit reached", 400, error_data)
                raise HeyGenAPIError(f"Bad request: {error_data}", 400, error_data)
            elif e.response.status_code >= 500:
                logger.error("Server error", status_code=e.response.status_code)
                raise HeyGenAPIError(f"Server error: {e.response.status_code}", e.response.status_code)
            else:
                raise HeyGenAPIError(f"HTTP error: {e.response.status_code}", e.response.status_code)
        except httpx.RequestError as e:
            logger.error("Network error", error=str(e))
            raise HeyGenAPIError(f"Network error: {str(e)}")
    
    return wrapper