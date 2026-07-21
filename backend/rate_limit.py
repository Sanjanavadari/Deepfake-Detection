from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

RATE_LIMIT_EXCEEDED_DETAIL = (
    "Too many requests from your network. Please wait a minute and try again."
)

limiter = Limiter(key_func=get_remote_address)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": RATE_LIMIT_EXCEEDED_DETAIL},
        headers={"Retry-After": str(exc.retry_after)},
    )
