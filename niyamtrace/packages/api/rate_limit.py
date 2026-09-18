from fastapi import Request
from packages.api.errors import NiyamAPIError
from packages.auth import Principal

# Simple in-memory counters for demonstration (in production use Redis)
_tenant_limits = {}
_principal_limits = {}
_global_requests = 0

MAX_GLOBAL_REQUESTS = 1000 # inflight limit
MAX_TENANT_RATE = 100 # requests per minute
MAX_PRINCIPAL_RATE = 20 # requests per minute

class RateLimiter:
    """
    Basic rate limiter module for Phase 4.
    """
    @classmethod
    def check_global(cls):
        global _global_requests
        if _global_requests >= MAX_GLOBAL_REQUESTS:
            raise NiyamAPIError(status_code=503, code="SERVER_OVERLOAD", message="Server is overloaded.")

    @classmethod
    def increment_global(cls):
        global _global_requests
        _global_requests += 1
        
    @classmethod
    def decrement_global(cls):
        global _global_requests
        _global_requests = max(0, _global_requests - 1)

    @classmethod
    def check_tenant(cls, tenant_id: str):
        # Dummy logic, in real life we use a sliding window counter
        pass
        
    @classmethod
    def check_principal(cls, principal: Principal):
        # Dummy logic, in real life we use a sliding window counter
        pass

async def rate_limit_dependency(request: Request):
    """
    Dependency to enforce rate limits per request.
    Throws 429 Too Many Requests if limits exceeded.
    """
    RateLimiter.check_global()
    
    # We can check tenant / principal rate limits here 
    # if we have the principal from context
    
    # If exceeded:
    # raise NiyamAPIError(status_code=429, code="RATE_LIMIT_EXCEEDED", message="Too many requests")
    pass
