import multiprocessing
import os
from config import settings

# Server socket
bind = f"{settings.host}:{settings.port}"
backlog = 2048

# Worker processes
workers = settings.workers or multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# Timeout settings
timeout = 30
keepalive = 2
graceful_timeout = 30

# Logging
accesslog = "./logs/access.log"
errorlog = "./logs/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "jarvistrade"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# SSL (uncomment for HTTPS)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Development settings (override in production)
if settings.environment == "development":
    reload = True
    reload_extra_files = [
        "./",
        "./main.py",
        "./models.py",
        "./schemas.py"
    ]
else:
    reload = False

# Production optimizations
if settings.environment == "production":
    # Disable access log in production if not needed
    # accesslog = None
    
    # Enable worker recycling
    max_requests = 1000
    max_requests_jitter = 100
    
    # Security headers
    secure_scheme_headers = {
        'X-FORWARDED-PROTOCOL': 'ssl',
        'X-FORWARDED-PROTO': 'https',
        'X-FORWARDED-SSL': 'on'
    }
    
    # Trusted proxies
    forwarded_allow_ips = '*'

# Health check endpoint
def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_worker_init(worker):
    worker.log.info("Worker initialized (pid: %s)", worker.pid)

def worker_abort(worker):
    worker.log.info("Worker aborted (pid: %s)", worker.pid)

