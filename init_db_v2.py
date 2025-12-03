"""
Initialize database with v2 schema
"""
from models_v2 import Base
from sqlalchemy import create_engine
from config import settings

print(f"Creating v2 database at: {settings.database_url}")
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {})

# Create all tables
Base.metadata.create_all(bind=engine)

print("✅ Database created successfully with v2 schema!")
print("\nTables created:")
for table in Base.metadata.sorted_tables:
    print(f"  - {table.name}")
