import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings

logger = logging.getLogger("fitcheck.database")

engine = None
SessionLocal = None
Base = declarative_base()

def get_engine():
    global engine, SessionLocal
    if engine is not None:
        return engine

    # First attempt: Primary DATABASE_URL (e.g. PostgreSQL)
    try:
        logger.info(f"Connecting to database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
        test_engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 5} if "postgresql" in settings.DATABASE_URL else {}
        )
        # Test connection
        with test_engine.connect() as conn:
            pass
        engine = test_engine
        logger.info("Successfully connected to primary database.")
    except Exception as e:
        logger.warning(f"Failed to connect to primary database: {e}")
        if settings.SQLITE_FALLBACK:
            fallback_url = "sqlite:///./fitcheck.db"
            logger.info(f"Falling back to local SQLite database: {fallback_url}")
            engine = create_engine(fallback_url, connect_args={"check_same_thread": False})
        else:
            raise e

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine

def get_db():
    get_engine()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    eng = get_engine()
    try:
        from . import models  # noqa: F401
    except (ImportError, ValueError):
        import app.models  # noqa: F401
    Base.metadata.create_all(bind=eng)
    logger.info("Database tables verified/created successfully.")
