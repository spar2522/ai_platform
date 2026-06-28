class AIProviderException(Exception):
    pass


class AuthenticationException(AIProviderException):
    pass


class RateLimitException(AIProviderException):
    pass


class TimeoutException(AIProviderException):
    pass
