"""Structured logging configuration."""

import logging
import sys
from typing import Any, Dict
import structlog
from structlog.typing import EventDict, Processor

def setup_logging(log_level: str = "INFO") -> None:
    """Configure structured logging for the application."""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.ConsoleRenderer() if sys.stdout.isatty() else structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        logger_factory=structlog.WriteLoggerFactory(),
        context_class=dict,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

def get_logger(name: str) -> Any:
    """Get a structured logger instance."""
    return structlog.get_logger(name)

# Metrics collection
class MetricsCollector:
    """Simple metrics collector for monitoring."""
    
    def __init__(self):
        self.metrics: Dict[str, int] = {}
    
    def increment(self, metric: str, value: int = 1) -> None:
        """Increment a counter metric."""
        self.metrics[metric] = self.metrics.get(metric, 0) + value
    
    def get_metrics(self) -> Dict[str, int]:
        """Get all collected metrics."""
        return self.metrics.copy()

# Global metrics instance
metrics = MetricsCollector()