from fastapi import Request, HTTPException
from app.redis_client import redis_client
from app.config import settings
import time

async def rate_limit_middleware(request: Request):
    # Skip rate limiting for health checks
    if request.url.path == "/health":
        return

    client_ip = request.client.host
    current_minute = int(time.time() / 60)
    key = f"rate_limit:{client_ip}:{current_minute}"
    
    count = redis_client.incr(key)
    if count == 1:
        redis_client.expire(key, 60)
    
    if count > settings.RATE_LIMIT_PER_MINUTE:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
