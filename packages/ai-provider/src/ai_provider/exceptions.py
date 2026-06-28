class AIProviderException(Exception):
    """Base exception class for AI provider-related errors."""
    pass


class AuthenticationException(AIProviderException):
    """Exception raised when authentication fails."""
    pass


class RateLimitException(AIProviderException):
    """Exception raised when rate limits are exceeded."""
    pass


class TimeoutException(AIProviderException):
    """Exception raised when operations time out."""
    pass