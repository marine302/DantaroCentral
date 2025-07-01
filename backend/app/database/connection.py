"""
Database connection and session management for Dantaro Central.
"""
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.core.config import settings
from app.models.database import Base


# Synchronous database engine
sync_engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.is_development,
)

# Create synchronous session factory
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=sync_engine
)


def get_sync_db() -> Generator[Session, None, None]:
    """
    Dependency for getting synchronous database session.
    For use in worker processes and synchronous contexts.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=sync_engine)


def drop_tables():
    """Drop all database tables. Use with caution!"""
    Base.metadata.drop_all(bind=sync_engine)


def init_db():
    """Initialize database with tables."""
    create_tables()
    print("Database tables created successfully!")


if __name__ == "__main__":
    # For direct execution - create tables
    init_db()
