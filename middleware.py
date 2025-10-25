import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 10, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.client = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        now = time.time()
        request_times = self.client.get(client_ip, [])
        request_times = [t for t in request_times if now - t < self.window_seconds]
        if len(request_times) >= self.max_requests:
            return JSONResponse(status_code=429, content={"message": "Too many requests, try again later."})
        request_times.append(now)
        self.client[client_ip] = request_times
        response = await call_next(request)
        return response
