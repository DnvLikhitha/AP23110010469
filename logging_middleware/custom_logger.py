import time
import os
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class CustomLogger:
    def __init__(self, log_file="app.log"):
        self.log_file = log_file
    
    def log(self, level, message):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        with open(self.log_file, "a") as f:
            f.write(log_entry)

    def info(self, message):
        self.log("INFO", message)

    def error(self, message):
        self.log("ERROR", message)

    def debug(self, message):
        self.log("DEBUG", message)

logger = CustomLogger()

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        logger.info(f"Received request: {request.method} {request.url}")
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        logger.info(f"Response status: {response.status_code} - Completed in {process_time:.4f}s")
        
        return response
