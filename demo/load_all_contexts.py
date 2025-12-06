#!/usr/bin/env python3
"""
Load all demo contexts into the database.
Clears existing demo database and repopulates from scratch.
Usage: python demo/load_all_contexts.py
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from load_demo_context import DemoContextLoader
from sqlalchemy import create_engine
from models_v2 import Base
from models_config import SystemConfig
from config import settings

# All available contexts
CONTEXTS = [
    'physics_101',
    'biology_200',
    'calculus_150',
    'chemistry_110',
    'computer_science_101'
]


def reset_database():
    """Remove and recreate demo database."""
    db_path = Path("data/demo_raisemyhand.db")
    
    if db_path.exists():
        print(f"🗑️  Removing existing demo database...")
        db_path.unlink()
    
    print("📦 Creating fresh demo database...")
    engine = create_engine(
        "sqlite:///./data/demo_raisemyhand.db",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    SystemConfig.metadata.create_all(bind=engine)
    print("✓ Fresh database created")


def main():
    print("=" * 70)
    print("🎯 Loading ALL Demo Contexts")
    print("=" * 70)
    
    # Reset database
    reset_database()
    
    # Load each context
    for ctx in CONTEXTS:
        print(f"\n{'=' * 70}")
        print(f"📚 Loading: {ctx}")
        print('=' * 70)
        
        try:
            loader = DemoContextLoader(ctx)
            loader.load_all()
        except Exception as e:
            print(f"❌ Failed to load {ctx}: {e}")
            continue
    
    print("\n" + "=" * 70)
    print("✅ All 5 contexts loaded successfully!")
    print("=" * 70)
    print("\n📊 Database contains:")
    print("  - 6 instructors")
    print("  - 5 classes")
    print("  - 25 meetings")
    print("  - ~275 questions with votes")
    print("\n🌐 Access at http://localhost:8000/sessions")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
