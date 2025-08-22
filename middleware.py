from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import time
import logging
from typing import Callable
from config import settings
import redis
import json

# Configure logging
logger = logging.getLogger(__name__)

# Redis client for rate limiting
redis_client = None
try:
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    redis_client.ping()
except Exception as e:
    logger.warning(f"Redis connection failed: {e}. Rate limiting will be disabled.")
    redis_client = None

class RateLimitMiddleware:
    """Rate limiting middleware using Redis"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Get client IP
        client_ip = self._get_client_ip(scope)
        
        # Check rate limit
        if not self._check_rate_limit(client_ip):
            response = Response(
                content=json.dumps({"error": "Rate limit exceeded"}),
                status_code=429,
                media_type="application/json"
            )
            await response(scope, receive, send)
            return
        
        await self.app(scope, receive, send)
    
    def _get_client_ip(self, scope):
        """Extract client IP from request"""
        headers = dict(scope.get("headers", []))
        
        # Check for forwarded headers
        if b"x-forwarded-for" in headers:
            return headers[b"x-forwarded-for"].decode().split(",")[0].strip()
        
        # Check for real IP header
        if b"x-real-ip" in headers:
            return headers[b"x-real-ip"].decode()
        
        # Fallback to client address
        return scope.get("client", ("", ""))[0]
    
    def _check_rate_limit(self, client_ip):
        """Check if client has exceeded rate limit"""
        if not redis_client:
            return True  # Allow if Redis is not available
        
        try:
            # Per-minute rate limit
            minute_key = f"rate_limit:{client_ip}:minute"
            minute_count = redis_client.get(minute_key)
            
            if minute_count and int(minute_count) >= settings.rate_limit_per_minute:
                return False
            
            # Per-hour rate limit
            hour_key = f"rate_limit:{client_ip}:hour"
            hour_count = redis_client.get(hour_key)
            
            if hour_count and int(hour_count) >= settings.rate_limit_per_hour:
                return False
            
            # Increment counters
            pipe = redis_client.pipeline()
            pipe.incr(minute_key)
            pipe.expire(minute_key, 60)
            pipe.incr(hour_key)
            pipe.expire(hour_key, 3600)
            pipe.execute()
            
            return True
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            return True  # Allow if rate limiting fails

class SecurityHeadersMiddleware:
    """Add security headers to responses"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                
                # Security headers
                security_headers = {
                    b"x-content-type-options": b"nosniff",
                    b"x-frame-options": b"DENY",
                    b"x-xss-protection": b"1; mode=block",
                    b"referrer-policy": b"strict-origin-when-cross-origin",
                    b"permissions-policy": b"geolocation=(), microphone=(), camera=()",
                }
                
                # Add HSTS header in production
                if settings.environment == "production":
                    security_headers[b"strict-transport-security"] = b"max-age=31536000; includeSubDomains"
                
                # Add security headers
                for key, value in security_headers.items():
                    headers.append((key, value))
                
                message["headers"] = headers
            
            await send(message)
        
        await self.app(scope, receive, send_with_headers)

class RequestLoggingMiddleware:
    """Log all requests for monitoring"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        
        # Log request start
        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "UNKNOWN")
        client_ip = self._get_client_ip(scope)
        
        logger.info(f"Request started: {method} {path} from {client_ip}")
        
        async def send_with_logging(message):
            if message["type"] == "http.response.end":
                duration = time.time() - start_time
                status = getattr(message, "status", "UNKNOWN")
                logger.info(f"Request completed: {method} {path} - {status} in {duration:.3f}s")
            
            await send(message)
        
        await self.app(scope, receive, send_with_logging)
    
    def _get_client_ip(self, scope):
        """Extract client IP from request"""
        headers = dict(scope.get("headers", []))
        
        if b"x-forwarded-for" in headers:
            return headers[b"x-forwarded-for"].decode().split(",")[0].strip()
        
        if b"x-real-ip" in headers:
            return headers[b"x-real-ip"].decode()
        
        return scope.get("client", ("", ""))[0]

def setup_middleware(app):
    """Setup all middleware for the application"""
    
    # Trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Gzip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Custom middleware
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)
    
    return app

