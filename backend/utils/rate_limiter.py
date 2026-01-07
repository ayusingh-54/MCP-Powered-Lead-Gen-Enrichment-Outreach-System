"""
Rate Limiter and Retry Logic
============================
Provides rate limiting and retry mechanisms for the outreach system.
Ensures compliance with sending limits and graceful error handling.
"""

import time
import asyncio
from datetime import datetime, timedelta
from typing import Callable, TypeVar, Optional, Any
from functools import wraps
from collections import deque
import logging

logger = logging.getLogger("leadgen.utils.rate_limiter")

T = TypeVar("T")


class RateLimiter:
    """
    Token bucket rate limiter for controlling message sending rate.
    Thread-safe implementation using a sliding window approach.
    """
    
    def __init__(self, max_requests: int = 10, time_window: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed in the time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: deque = deque()
        self._lock = asyncio.Lock() if asyncio.get_event_loop().is_running() else None
    
    def _clean_old_requests(self):
        """Remove requests outside the current time window."""
        cutoff = datetime.utcnow() - timedelta(seconds=self.time_window)
        while self.requests and self.requests[0] < cutoff:
            self.requests.popleft()
    
    def can_proceed(self) -> bool:
        """
        Check if a request can proceed without blocking.
        
        Returns:
            True if request can proceed immediately
        """
        self._clean_old_requests()
        return len(self.requests) < self.max_requests
    
    def wait_time(self) -> float:
        """
        Calculate time to wait before next request is allowed.
        
        Returns:
            Seconds to wait (0 if can proceed immediately)
        """
        self._clean_old_requests()
        
        if len(self.requests) < self.max_requests:
            return 0.0
        
        # Calculate when the oldest request will expire
        oldest = self.requests[0]
        expiry = oldest + timedelta(seconds=self.time_window)
        wait = (expiry - datetime.utcnow()).total_seconds()
        
        return max(0.0, wait)
    
    def acquire(self) -> bool:
        """
        Acquire a rate limit slot, blocking if necessary.
        
        Returns:
            True when slot is acquired
        """
        wait = self.wait_time()
        if wait > 0:
            logger.debug(f"Rate limit reached, waiting {wait:.2f}s")
            time.sleep(wait)
        
        self._clean_old_requests()
        self.requests.append(datetime.utcnow())
        return True
    
    async def acquire_async(self) -> bool:
        """
        Async version of acquire.
        
        Returns:
            True when slot is acquired
        """
        wait = self.wait_time()
        if wait > 0:
            logger.debug(f"Rate limit reached, waiting {wait:.2f}s")
            await asyncio.sleep(wait)
        
        self._clean_old_requests()
        self.requests.append(datetime.utcnow())
        return True
    
    def get_status(self) -> dict:
        """
        Get current rate limiter status.
        
        Returns:
            Dict with rate limiter state
        """
        self._clean_old_requests()
        return {
            "requests_in_window": len(self.requests),
            "max_requests": self.max_requests,
            "time_window_seconds": self.time_window,
            "can_proceed": self.can_proceed(),
            "wait_time_seconds": self.wait_time()
        }


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_retries: int = 2,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_backoff: bool = True,
        retry_exceptions: tuple = (Exception,)
    ):
        """
        Initialize retry configuration.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay between retries in seconds
            max_delay: Maximum delay between retries
            exponential_backoff: Use exponential backoff strategy
            retry_exceptions: Tuple of exceptions to retry on
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_backoff = exponential_backoff
        self.retry_exceptions = retry_exceptions


class RetryResult:
    """Result of a retry operation."""
    
    def __init__(
        self,
        success: bool,
        result: Any = None,
        attempts: int = 0,
        last_error: Optional[Exception] = None,
        total_time: float = 0.0
    ):
        self.success = success
        self.result = result
        self.attempts = attempts
        self.last_error = last_error
        self.total_time = total_time
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "attempts": self.attempts,
            "last_error": str(self.last_error) if self.last_error else None,
            "total_time_seconds": self.total_time
        }


def retry_with_backoff(config: RetryConfig = None):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        config: Retry configuration (uses defaults if None)
        
    Returns:
        Decorated function
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable[..., T]) -> Callable[..., RetryResult]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> RetryResult:
            start_time = time.time()
            last_error = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    return RetryResult(
                        success=True,
                        result=result,
                        attempts=attempt + 1,
                        total_time=time.time() - start_time
                    )
                except config.retry_exceptions as e:
                    last_error = e
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                    
                    if attempt < config.max_retries:
                        # Calculate delay
                        if config.exponential_backoff:
                            delay = min(config.base_delay * (2 ** attempt), config.max_delay)
                        else:
                            delay = config.base_delay
                        
                        logger.debug(f"Retrying in {delay:.2f}s...")
                        time.sleep(delay)
            
            return RetryResult(
                success=False,
                attempts=config.max_retries + 1,
                last_error=last_error,
                total_time=time.time() - start_time
            )
        
        return wrapper
    
    return decorator


async def retry_async(
    func: Callable,
    *args,
    config: RetryConfig = None,
    **kwargs
) -> RetryResult:
    """
    Retry an async function with backoff.
    
    Args:
        func: Async function to retry
        *args: Positional arguments for the function
        config: Retry configuration
        **kwargs: Keyword arguments for the function
        
    Returns:
        RetryResult with outcome
    """
    if config is None:
        config = RetryConfig()
    
    start_time = time.time()
    last_error = None
    
    for attempt in range(config.max_retries + 1):
        try:
            result = await func(*args, **kwargs)
            return RetryResult(
                success=True,
                result=result,
                attempts=attempt + 1,
                total_time=time.time() - start_time
            )
        except config.retry_exceptions as e:
            last_error = e
            logger.warning(f"Async attempt {attempt + 1} failed: {str(e)}")
            
            if attempt < config.max_retries:
                if config.exponential_backoff:
                    delay = min(config.base_delay * (2 ** attempt), config.max_delay)
                else:
                    delay = config.base_delay
                
                await asyncio.sleep(delay)
    
    return RetryResult(
        success=False,
        attempts=config.max_retries + 1,
        last_error=last_error,
        total_time=time.time() - start_time
    )


# =============================================================================
# GLOBAL RATE LIMITER INSTANCE
# =============================================================================

# Default rate limiter: 10 messages per minute
_default_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter(max_requests: int = 10, time_window: int = 60) -> RateLimiter:
    """
    Get or create the global rate limiter instance.
    
    Args:
        max_requests: Maximum requests per time window
        time_window: Time window in seconds
        
    Returns:
        RateLimiter instance
    """
    global _default_rate_limiter
    if _default_rate_limiter is None:
        _default_rate_limiter = RateLimiter(max_requests, time_window)
    return _default_rate_limiter


def reset_rate_limiter():
    """Reset the global rate limiter."""
    global _default_rate_limiter
    _default_rate_limiter = None
