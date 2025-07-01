"""
Production deployment configuration and utilities.
"""
import os
from typing import Dict, Any


def get_production_settings() -> Dict[str, Any]:
    """Get production environment settings."""
    return {
        "environment": "production",
        "debug": False,
        "docs_url": None,  # Disable API docs in production
        "redoc_url": None,
        "openapi_url": None,
        "cors_origins": os.getenv("CORS_ORIGINS", "").split(","),
        "database_url": os.getenv("DATABASE_URL"),
        "redis_url": os.getenv("REDIS_URL"),
        "secret_key": os.getenv("SECRET_KEY"),
        "log_level": "INFO",
    }


def get_staging_settings() -> Dict[str, Any]:
    """Get staging environment settings."""
    return {
        "environment": "staging",
        "debug": False,
        "docs_url": "/docs",  # Enable API docs in staging
        "redoc_url": "/redoc",
        "cors_origins": ["http://localhost:3000", "https://staging.dantaro.com"],
        "log_level": "DEBUG",
    }


def get_development_settings() -> Dict[str, Any]:
    """Get development environment settings."""
    return {
        "environment": "development",
        "debug": True,
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "cors_origins": ["*"],  # Allow all origins in development
        "log_level": "DEBUG",
        "reload": True,
    }
