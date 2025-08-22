import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Database Configuration
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./jarvistrade.db")
    database_url_test: str = os.getenv("DATABASE_URL_TEST", "sqlite:///./test.db")
    
    # Redis Configuration
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_password: Optional[str] = os.getenv("REDIS_PASSWORD")
    
    # Security Configuration
    secret_key: str = os.getenv("SECRET_KEY", "your-super-secret-key-here-change-in-production")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    refresh_token_expire_days: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # CORS Configuration
    allowed_origins: List[str] = os.getenv("ALLOWED_ORIGINS", os.getenv("FRONTEND_URL", "http://localhost:3000")).split(",")
    allowed_hosts: List[str] = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    
    # Email Configuration
    smtp_server: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    email_from: str = os.getenv("EMAIL_FROM", "noreply@yourdomain.com")
    
    # Payment Configuration
    paystack_secret_key: str = os.getenv("PAYSTACK_SECRET_KEY", "")
    paystack_public_key: str = os.getenv("PAYSTACK_PUBLIC_KEY", "")
    
    # File Storage Configuration
    upload_dir: str = os.getenv("UPLOAD_DIR", "./uploads")
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    allowed_extensions: List[str] = os.getenv("ALLOWED_EXTENSIONS", ".jpg,.jpeg,.png,.gif,.pdf,.txt,.zip,.ex5").split(",")
    
    # Logging Configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "./logs/app.log")
    log_max_size: int = int(os.getenv("LOG_MAX_SIZE", "10485760"))  # 10MB
    log_backup_count: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    
    # Production Configuration
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    environment: str = os.getenv("ENVIRONMENT", "development")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    workers: int = int(os.getenv("WORKERS", "4"))
    
    # Monitoring and Health Checks
    health_check_endpoint: str = os.getenv("HEALTH_CHECK_ENDPOINT", "/health")
    metrics_endpoint: str = os.getenv("METRICS_ENDPOINT", "/metrics")
    
    # Rate Limiting
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
    rate_limit_per_hour: int = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))
    
    # Session Configuration
    session_secret_key: str = os.getenv("SESSION_SECRET_KEY", "your-session-secret-key")
    session_expire_seconds: int = int(os.getenv("SESSION_EXPIRE_SECONDS", "3600"))
    
    # Backup Configuration
    backup_enabled: bool = os.getenv("BACKUP_ENABLED", "True").lower() == "true"
    backup_schedule: str = os.getenv("BACKUP_SCHEDULE", "0 2 * * *")  # Daily at 2 AM
    backup_retention_days: int = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
    
    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v):
        # Only validate length, allow default key for development
        if len(v) < 16:
            raise ValueError("Secret key must be at least 16 characters long")
        return v
    
    @field_validator('database_url')
    @classmethod
    def validate_database_url(cls, v, info):
        # Get environment from info.data if available
        environment = info.data.get('environment', 'development') if info.data else 'development'
        if environment == "production" and "sqlite" in v:
            raise ValueError("SQLite is not recommended for production. Use PostgreSQL or MySQL")
        return v
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"
    }

# Create global settings instance
settings = Settings()

# Environment-specific database URL
def get_database_url() -> str:
    """Get the appropriate database URL based on environment"""
    if settings.environment == "test":
        return settings.database_url_test
    return settings.database_url

# Validate production settings
def validate_production_settings():
    """Validate that production settings are properly configured"""
    if settings.environment == "production":
        if settings.debug:
            raise ValueError("DEBUG should be False in production")
        if "sqlite" in settings.database_url:
            raise ValueError("SQLite is not recommended for production")
        if settings.secret_key == "your-super-secret-key-here-change-in-production":
            raise ValueError("Please change the default secret key in production")
        if not settings.smtp_username or not settings.smtp_password:
            raise ValueError("SMTP credentials are required in production")
        if not settings.paystack_secret_key:
            raise ValueError("Payment service credentials are required in production")

