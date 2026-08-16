"""
LexIntellectus ERP - Rate Limiting
"""
from fastapi_limiter.depends import RateLimiter

# Define rate limiters for different endpoints
# Login: Max 5 requests per minute per IP
login_rate_limiter = RateLimiter(times=5, minutes=1)

# Default API: Max 100 requests per minute per IP
default_rate_limiter = RateLimiter(times=100, minutes=1)
