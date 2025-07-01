"""
Database migration and setup script for Dantaro Central.
"""
import sys
import logging
from pathlib import Path

# Add the backend directory to Python path
backend_path = Path(__file__).parent.parent
sys.path.append(str(backend_path))

from app.database.connection import init_db, create_tables, drop_tables
from app.database.redis_cache import redis_manager
from app.models.database import Base


def setup_logging():
    """로깅 설정."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def check_database_connection():
    """데이터베이스 연결 확인."""
    try:
        from app.database.connection import sync_engine
        from sqlalchemy import text
        with sync_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        return False


def check_redis_connection():
    """Redis 연결 확인."""
    try:
        if redis_manager.health_check():
            logging.info("Redis connection successful")
            return True
        else:
            logging.error("Redis connection failed")
            return False
    except Exception as e:
        logging.error(f"Redis connection error: {e}")
        return False


def migrate_database():
    """데이터베이스 마이그레이션 실행."""
    try:
        logging.info("Starting database migration...")
        
        # 1. 연결 확인
        if not check_database_connection():
            logging.error("Database connection failed. Please check your database configuration.")
            return False
        
        # 2. 테이블 생성
        logging.info("Creating database tables...")
        create_tables()
        logging.info("Database tables created successfully!")
        
        # 3. Redis 연결 확인
        if check_redis_connection():
            logging.info("Redis cache is ready")
        else:
            logging.warning("Redis connection failed, but database migration completed")
        
        return True
        
    except Exception as e:
        logging.error(f"Migration failed: {e}")
        return False


def reset_database():
    """데이터베이스 초기화 (모든 데이터 삭제)."""
    try:
        logging.warning("WARNING: This will delete all data!")
        confirm = input("Are you sure you want to reset the database? (yes/no): ")
        
        if confirm.lower() != 'yes':
            logging.info("Database reset cancelled")
            return False
        
        logging.info("Dropping all tables...")
        drop_tables()
        
        logging.info("Recreating tables...")
        create_tables()
        
        logging.info("Database reset completed!")
        return True
        
    except Exception as e:
        logging.error(f"Database reset failed: {e}")
        return False


def main():
    """메인 함수."""
    setup_logging()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python migrate.py migrate    - Run database migration")
        print("  python migrate.py reset      - Reset database (delete all data)")
        print("  python migrate.py check      - Check database connection")
        return
    
    command = sys.argv[1]
    
    if command == "migrate":
        if migrate_database():
            logging.info("✅ Database migration completed successfully!")
        else:
            logging.error("❌ Database migration failed!")
            sys.exit(1)
    
    elif command == "reset":
        if reset_database():
            logging.info("✅ Database reset completed successfully!")
        else:
            logging.error("❌ Database reset failed!")
            sys.exit(1)
    
    elif command == "check":
        logging.info("Checking database connection...")
        if check_database_connection():
            logging.info("✅ Database connection successful!")
        else:
            logging.error("❌ Database connection failed!")
            sys.exit(1)
        
        if check_redis_connection():
            logging.info("✅ Redis connection successful!")
        else:
            logging.error("❌ Redis connection failed!")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
