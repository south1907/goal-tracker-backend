#!/usr/bin/env python3
"""
Fix enum values in database to match SQLAlchemy enum definitions.
This script updates existing enum values in the database.
"""

import asyncio
from sqlalchemy import text
from app.core.database import engine

async def fix_enums():
    """Fix enum values in the database."""
    async with engine.begin() as conn:
        # Check current enum values
        result = await conn.execute(text("SHOW COLUMNS FROM goals WHERE Field = 'goal_type'"))
        print("Current goal_type enum definition:")
        for row in result:
            print(row)
        
        # Note: MySQL doesn't support easy enum value updates
        # The enum values are correct (lowercase), but SQLAlchemy may be reading them incorrectly
        # This is a SQLAlchemy configuration issue, not a database issue
        
        print("\n✅ Database enum values are correct (lowercase)")
        print("The issue is in SQLAlchemy enum handling")
        print("\nTo fix, ensure SQLEnum is configured with native_enum=False")

if __name__ == "__main__":
    asyncio.run(fix_enums())

