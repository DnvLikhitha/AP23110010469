import os
import requests
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
LOG_API_URL = "http://20.207.122.201/evaluation-service/logs"

AUTH_HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

def log(stack: str, level: str, package: str, message: str):
    payload = {
        "stack": stack.lower(),
        "level": level.lower(),
        "package": package.lower(),
        "message": message
    }
    
    try:
        response = requests.post(LOG_API_URL, json=payload, headers=AUTH_HEADERS)
        
        # If the token expires or network errors occur, we print locally to not break the app
        if response.status_code != 200:
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
            with open("app_execution_fallback.log", "a") as f:
                f.write(f"[{current_time}] API LOG FAILED (Status {response.status_code}): {payload}\n")
    except Exception as e:
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        with open("app_execution_fallback.log", "a") as f:
            f.write(f"[{current_time}] EXCEPTION in Log API: {str(e)}\n")

class AppLogger:
    # We define the package as 'handler' for general business logic or 'service'
    def info(self, msg, package="handler"):
        log("backend", "info", package, msg)
        
    def error(self, msg, package="handler"):
        log("backend", "error", package, msg)
        
    def debug(self, msg, package="handler"):
        log("backend", "debug", package, msg)
        
    def fatal(self, msg, package="handler"):
        log("backend", "fatal", package, msg)

# Create a global instance
app_logger = AppLogger()

class CustomLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        log("backend", "info", "middleware", f"Incoming Request -> Method: {request.method} Path: {request.url.path}")
        
        start_time = time.time()
        response = await call_next(request)
        end_time = time.time()
        
        duration = round(end_time - start_time, 4)
        status = response.status_code
        
        if status >= 500:
            level = "error"
        elif status >= 400:
            level = "warn"
        else:
            level = "info"
            
        log("backend", level, "middleware", f"Request Completed -> Status: {status}, Took: {duration}s")
        return response