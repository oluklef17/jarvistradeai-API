from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db, check_database_health
from config import settings
import redis
import psutil
import os
from datetime import datetime
from typing import Dict, Any

router = APIRouter()

# Redis client for health checks
redis_client = None
try:
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    redis_client.ping()
except Exception:
    redis_client = None

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment,
        "version": "1.0.0"
    }

@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check including all services"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment,
        "version": "1.0.0",
        "services": {}
    }
    
    overall_status = "healthy"
    
    # Database health
    try:
        db_healthy = check_database_health()
        health_status["services"]["database"] = {
            "status": "healthy" if db_healthy else "unhealthy",
            "type": "postgresql" if "postgresql" in settings.database_url else "sqlite"
        }
        if not db_healthy:
            overall_status = "degraded"
    except Exception as e:
        health_status["services"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_status = "unhealthy"
    
    # Redis health
    try:
        if redis_client:
            redis_client.ping()
            health_status["services"]["redis"] = {
                "status": "healthy",
                "type": "redis"
            }
        else:
            health_status["services"]["redis"] = {
                "status": "unavailable",
                "type": "redis"
            }
    except Exception as e:
        health_status["services"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        if overall_status == "healthy":
            overall_status = "degraded"
    
    # System resources
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_status["services"]["system"] = {
            "status": "healthy",
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "disk_percent": disk.percent
        }
        
        # Check if system resources are critical
        if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
            health_status["services"]["system"]["status"] = "warning"
            if overall_status == "healthy":
                overall_status = "degraded"
    except Exception as e:
        health_status["services"]["system"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_status = "unhealthy"
    
    # File system health
    try:
        upload_dir = settings.upload_dir
        if os.path.exists(upload_dir):
            dir_size = sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, dirnames, filenames in os.walk(upload_dir)
                for filename in filenames
            )
            
            health_status["services"]["file_system"] = {
                "status": "healthy",
                "upload_dir_size_mb": round(dir_size / (1024 * 1024), 2)
            }
        else:
            health_status["services"]["file_system"] = {
                "status": "warning",
                "upload_dir": "not_found"
            }
            if overall_status == "healthy":
                overall_status = "degraded"
    except Exception as e:
        health_status["services"]["file_system"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_status = "unhealthy"
    
    health_status["status"] = overall_status
    
    return health_status

@router.get("/health/ready")
async def readiness_check():
    """Readiness check for Kubernetes/container orchestration"""
    try:
        # Check if database is accessible
        db_healthy = check_database_health()
        
        # Check if Redis is accessible (if configured)
        redis_healthy = True
        if redis_client:
            try:
                redis_client.ping()
            except Exception:
                redis_healthy = False
        
        # Application is ready if database is healthy
        if db_healthy:
            return {
                "status": "ready",
                "timestamp": datetime.utcnow().isoformat(),
                "database": "ready",
                "redis": "ready" if redis_healthy else "not_configured"
            }
        else:
            return {
                "status": "not_ready",
                "timestamp": datetime.utcnow().isoformat(),
                "database": "not_ready",
                "redis": "ready" if redis_healthy else "not_configured"
            }
    except Exception as e:
        return {
            "status": "not_ready",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

@router.get("/health/live")
async def liveness_check():
    """Liveness check for Kubernetes/container orchestration"""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "pid": os.getpid()
    }

@router.get("/metrics")
async def metrics():
    """Basic metrics endpoint for monitoring"""
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Process metrics
        process = psutil.Process()
        process_memory = process.memory_info()
        
        metrics_data = {
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2)
            },
            "process": {
                "memory_rss_mb": round(process_memory.rss / (1024**2), 2),
                "memory_vms_mb": round(process_memory.vms / (1024**2), 2),
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads(),
                "num_fds": process.num_fds() if hasattr(process, 'num_fds') else None
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return metrics_data
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

