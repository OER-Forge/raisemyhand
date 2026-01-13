from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from models_v2 import Base  # V2 schema
from config import settings

DATABASE_URL = settings.database_url

# Configure connection pooling based on database type
if "sqlite" in DATABASE_URL:
    # SQLite: Use QueuePool with reasonable limits for concurrent access
    # Note: SQLite still has database-level write locks, but this improves read concurrency
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "check_same_thread": False,
            "timeout": 30  # Wait up to 30 seconds for database lock
        },
        poolclass=QueuePool,
        pool_size=10,           # Allow 10 concurrent connections
        max_overflow=20,        # Allow 20 extra connections when pool exhausted
        pool_pre_ping=True,     # Verify connections before use
        pool_recycle=3600       # Recycle connections after 1 hour
    )

    # Enable WAL mode for better concurrency (allows concurrent reads during writes)
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
        cursor.close()
else:
    # PostgreSQL: Use default QueuePool with production settings
    engine = create_engine(
        DATABASE_URL,
        pool_size=20,          # 20 persistent connections
        max_overflow=10,       # Allow 10 overflow connections
        pool_pre_ping=True,    # Verify connections before use
        pool_recycle=3600      # Recycle connections after 1 hour
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize the database, creating all tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for getting database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
