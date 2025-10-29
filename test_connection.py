#!/usr/bin/env python3
"""
Test MySQL connection script.
"""

import asyncio
import aiomysql

async def test_connection():
    """Test MySQL connection."""
    try:
        conn = await aiomysql.connect(
            host='localhost',
            port=3306,
            user='root',
            password='123456aA@',
            db='goals'
        )
        
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT 1")
            result = await cursor.fetchone()
            print(f"✅ Connection successful! Result: {result}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())
