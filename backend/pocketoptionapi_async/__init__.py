"""
Professional Async PocketOption API - Core module
Fully async implementation with modern Python practices
"""

from .client import AsyncPocketOptionClient
from .constants import ASSETS, Regions
from .exceptions import (
    AuthenticationError,
    ConnectionError,
    InvalidParameterError,
    OrderError,
    PocketOptionError,
    TimeoutError,
    WebSocketError,
)
from .models import (
    Asset,
    Balance,
    Candle,
    ConnectionStatus,
    Order,
    OrderDirection,
    OrderResult,
    OrderStatus,
)

# Import monitoring components
from .monitoring import (
    CircuitBreaker,
    ErrorCategory,
    ErrorMonitor,
    ErrorSeverity,
    HealthChecker,
    RetryPolicy,
    error_monitor,
    health_checker,
)

# Create REGIONS instance
REGIONS = Regions()

__version__ = "2.0.0"
__author__ = "PocketOptionAPI Team"

__all__ = [
    "AsyncPocketOptionClient",
    "PocketOptionError",
    "ConnectionError",
    "AuthenticationError",
    "OrderError",
    "TimeoutError",
    "InvalidParameterError",
    "WebSocketError",
    "Balance",
    "Candle",
    "Order",
    "OrderResult",
    "OrderStatus",
    "OrderDirection",
    "Asset",
    "ConnectionStatus",
    "ASSETS",
    "REGIONS",
    "ErrorMonitor",
    "HealthChecker",
    "ErrorSeverity",
    "ErrorCategory",
    "CircuitBreaker",
    "RetryPolicy",
    "error_monitor",
    "health_checker",
]
