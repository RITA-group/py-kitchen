from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request


class CacheControlHeader(BaseHTTPMiddleware):
    def __init__(self, app, header_value='no-store'):
        super().__init__(app)
        self.header_value = header_value

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = self.header_value
        return response
