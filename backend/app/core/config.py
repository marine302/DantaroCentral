"""
Core configuration settings for Dantaro Central server.
"""
from typing import List, Optional
from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    api_v1_str: str = "/api/v1"
    project_name: str = "Dantaro Central"
    environment: str = "development"
    
    # Database
    database_url: str = "sqlite:///./dantaro_central.db"
    database_test_url: Optional[str] = None
    
    # Redis Cache
    redis_url: str = "redis://localhost:6379/0"
    
    # Security
    secret_key: str = "development-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # User Server Authentication
    user_server_api_key: str = "development-user-server-key"
    
    # External Exchange APIs
    coinbase_api_key: Optional[str] = None
    coinbase_api_secret: Optional[str] = None
    binance_api_key: Optional[str] = None
    binance_api_secret: Optional[str] = None
    upbit_access_key: Optional[str] = None
    upbit_secret_key: Optional[str] = None
    bithumb_api_key: Optional[str] = None
    bithumb_secret_key: Optional[str] = None
    korbit_api_key: Optional[str] = None
    korbit_secret_key: Optional[str] = None
    gopax_api_key: Optional[str] = None
    gopax_secret_key: Optional[str] = None
    coinone_access_token: Optional[str] = None
    
    # New Exchange APIs (Modularized Exchanges)
    okx_api_key: Optional[str] = None
    okx_secret_key: Optional[str] = None
    okx_passphrase: Optional[str] = None
    coinone_api_key: Optional[str] = None
    coinone_secret_key: Optional[str] = None
    gate_api_key: Optional[str] = None
    gate_secret_key: Optional[str] = None
    bybit_api_key: Optional[str] = None
    bybit_secret_key: Optional[str] = None
    
    # AI/ML Configuration
    ai_model_path: str = "./models"
    strategy_cache_ttl: int = 300
    
    # Background Tasks
    market_analysis_interval: int = 30  # 30 seconds for testing
    
    # Monitoring
    prometheus_port: int = 8001
    log_level: str = "DEBUG"
    
    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_seconds: int = 60
    
    # Market Analysis Settings
    support_level_lookback_days: int = 90
    recommendation_update_interval: int = 300  # 5 minutes
    top_recommendations_count: int = 50
    
    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v.startswith(("postgresql://", "postgresql+asyncpg://", "sqlite:///")):
            raise ValueError("Database URL must be PostgreSQL or SQLite")
        return v
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
