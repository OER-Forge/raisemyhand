"""
Centralized rate limiter configuration to avoid circular imports
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize rate limiter once, can be imported by multiple modules
limiter = Limiter(key_func=get_remote_address)
