"""
Core configuration and settings.
"""

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = Field(default="Goal Tracker Backend")
    APP_VERSION: str = Field(default="0.1.0")
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO")
    TZ: str = Field(default="Asia/Bangkok")
    
    # Database
    DATABASE_URL: str = Field(
        default="mysql+pymysql://goals:goalspassword@mysql:3306/goals"
    )
    DATABASE_URL_LOCAL: str = Field(
        default="mysql+pymysql://goals:goalspassword@localhost:3306/goals"
    )
    
    # JWT
    JWT_SECRET: str = Field(default="your-super-secret-jwt-key-change-this-in-production")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRE_MIN: int = Field(default=15)
    JWT_REFRESH_EXPIRE_DAYS: int = Field(default=14)
    
    # CORS
    CORS_ORIGINS: str = Field(default="http://localhost:3000,http://127.0.0.1:3000")
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True)
    
    # Security
    BCRYPT_ROUNDS: int = Field(default=12)
    RATE_LIMIT_ENABLED: bool = Field(default=True)
    RATE_LIMIT_REQUESTS: int = Field(default=100)
    RATE_LIMIT_WINDOW: int = Field(default=60)
    
    # MySQL
    MYSQL_ROOT_PASSWORD: str = Field(default="rootpassword")
    MYSQL_DATABASE: str = Field(default="goals")
    MYSQL_USER: str = Field(default="goals")
    MYSQL_PASSWORD: str = Field(default="goalspassword")
    
    # Redis (optional)
    REDIS_URL: str = Field(default="redis://redis:6379/0")
    
    # File upload
    MAX_FILE_SIZE: int = Field(default=10485760)  # 10MB
    ALLOWED_FILE_TYPES: str = Field(
        default="image/jpeg,image/png,image/gif,application/pdf"
    )
    
    # Email (optional)
    SMTP_HOST: str = Field(default="")
    SMTP_PORT: int = Field(default=587)
    SMTP_USERNAME: str = Field(default="")
    SMTP_PASSWORD: str = Field(default="")
    SMTP_FROM_EMAIL: str = Field(default="")
    
    # Monitoring
    SENTRY_DSN: str = Field(default="")
    HEALTH_CHECK_INTERVAL: int = Field(default=30)
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
