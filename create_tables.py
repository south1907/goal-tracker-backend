#!/usr/bin/env python3
"""
Create database tables directly without Alembic.
"""

import asyncio
from sqlalchemy import text
from app.core.database import engine
from app.models import Base

async def create_tables():
    """Create all database tables."""
    try:
        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            print("✅ All tables created successfully!")
            
            # Verify tables were created
            result = await conn.execute(text("SHOW TABLES"))
            tables = result.fetchall()
            print(f"📋 Created tables: {[table[0] for table in tables]}")
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")

if __name__ == "__main__":
    asyncio.run(create_tables())
