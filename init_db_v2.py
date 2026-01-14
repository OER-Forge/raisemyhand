"""
Initialize database with v2 schema
"""
import sys
from models_v2 import Base
from sqlalchemy import create_engine
from config import settings

# Validate production configuration before attempting database connection
if settings.is_production:
    print("\n🔐 Validating production configuration...")
    errors, warnings = settings.validate_production_config()

    if errors:
        print("\n❌ Production configuration errors:")
        for error in errors:
            print(f"   • {error}")
        print("\nPlease fix the above errors in .env.production before starting the application.")
        sys.exit(1)

    if warnings:
        print("\n⚠️  Production configuration warnings:")
        for warning in warnings:
            print(f"   • {warning}")

print(f"\n🗄️  Creating v2 database at: {settings.database_url}")

try:
    # Create engine with appropriate connection args for database type
    if "sqlite" in settings.database_url:
        engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False}
        )
    else:
        # PostgreSQL
        engine = create_engine(settings.database_url)

    # Create all tables
    Base.metadata.create_all(bind=engine)

    print("✅ Database initialized successfully with v2 schema!")
    print("\nTables created:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")

    print("\n✨ Ready for production deployment!")

except Exception as e:
    print(f"\n❌ Database initialization failed: {e}")
    print("\nTroubleshooting:")
    print("  • Verify DATABASE_URL is correct")
    print("  • For PostgreSQL: Check database server is running and credentials are valid")
    print("  • For SQLite: Check data directory exists and is writable")
    sys.exit(1)
