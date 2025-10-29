#!/usr/bin/env python3
"""
Simple script to create demo user and data directly in MySQL.
"""

import asyncio
import aiomysql
from datetime import datetime, timedelta
from decimal import Decimal

async def create_demo_data():
    """Create demo data directly in MySQL."""
    try:
        conn = await aiomysql.connect(
            host='localhost',
            port=3306,
            user='root',
            password='123456aA@',
            db='goals'
        )
        
        async with conn.cursor() as cursor:
            # Create demo user
            await cursor.execute("""
                INSERT IGNORE INTO users (email, password_hash, display_name, created_at)
                VALUES ('demo@local.test', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4/LewdBPj4', 'Demo User', NOW())
            """)
            
            # Get user ID
            await cursor.execute("SELECT id FROM users WHERE email = 'demo@local.test'")
            user_result = await cursor.fetchone()
            user_id = user_result[0]
            
            print(f"✅ Demo user created/found: demo@local.test (ID: {user_id})")
            
            # Create Goal A: Read 20 Books in 2025
            await cursor.execute("""
                INSERT IGNORE INTO goals (owner_id, name, description, emoji, goal_type, unit, target, 
                                        timeframe_type, start_at, end_at, privacy, status, created_at, updated_at)
                VALUES (%s, 'Read 20 Books in 2025', 'Read 20 books throughout the year 2025', '📚', 
                       'COUNT', 'books', 20, 'FIXED', '2025-01-01 00:00:00', '2025-12-31 23:59:59', 
                       'PRIVATE', 'ACTIVE', NOW(), NOW())
            """, (user_id,))
            
            # Get goal A ID
            await cursor.execute("SELECT id FROM goals WHERE name = 'Read 20 Books in 2025'")
            goal_a_result = await cursor.fetchone()
            goal_a_id = goal_a_result[0]
            
            print(f"✅ Goal A created: Read 20 Books in 2025 (ID: {goal_a_id})")
            
            # Create Goal B: Run 200 km in October
            await cursor.execute("""
                INSERT IGNORE INTO goals (owner_id, name, description, emoji, goal_type, unit, target, 
                                        timeframe_type, start_at, end_at, privacy, status, created_at, updated_at)
                VALUES (%s, 'Run 200 km in October', 'Run 200 kilometers during October 2025', '🏃', 
                       'SUM', 'km', 200, 'FIXED', '2025-10-01 00:00:00', '2025-10-31 23:59:59', 
                       'PRIVATE', 'ACTIVE', NOW(), NOW())
            """, (user_id,))
            
            # Get goal B ID
            await cursor.execute("SELECT id FROM goals WHERE name = 'Run 200 km in October'")
            goal_b_result = await cursor.fetchone()
            goal_b_id = goal_b_result[0]
            
            print(f"✅ Goal B created: Run 200 km in October (ID: {goal_b_id})")
            
            # Create Goal C: Daily Meditation Streak
            await cursor.execute("""
                INSERT IGNORE INTO goals (owner_id, name, description, emoji, goal_type, unit, target, 
                                        timeframe_type, start_at, rolling_days, privacy, status, created_at, updated_at)
                VALUES (%s, 'Daily Meditation Streak', 'Meditate every day for at least 10 minutes', '🧘', 
                       'STREAK', 'days', 30, 'ROLLING', DATE_SUB(NOW(), INTERVAL 30 DAY), 30, 
                       'PRIVATE', 'ACTIVE', NOW(), NOW())
            """, (user_id,))
            
            # Get goal C ID
            await cursor.execute("SELECT id FROM goals WHERE name = 'Daily Meditation Streak'")
            goal_c_result = await cursor.fetchone()
            goal_c_id = goal_c_result[0]
            
            print(f"✅ Goal C created: Daily Meditation Streak (ID: {goal_c_id})")
            
            # Create logs for Goal B
            logs_data = [
                (goal_b_id, user_id, '2025-10-03 10:00:00', 10, 'Morning run in the park'),
                (goal_b_id, user_id, '2025-10-07 08:00:00', 12, 'Long run along the river'),
                (goal_b_id, user_id, '2025-10-10 18:00:00', 8, 'Evening jog after work'),
            ]
            
            for log_data in logs_data:
                await cursor.execute("""
                    INSERT IGNORE INTO logs (goal_id, user_id, date, value, note, created_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                """, log_data)
            
            print(f"✅ Created {len(logs_data)} log entries for Goal B")
            
            # Create meditation logs for Goal C
            meditation_logs = []
            start_date = datetime.now() - timedelta(days=15)
            
            for i in range(15):  # 15 days of meditation
                log_date = start_date + timedelta(days=i)
                meditation_logs.append((
                    goal_c_id, user_id, log_date.strftime('%Y-%m-%d %H:%M:%S'), 1, f'Meditation session - Day {i+1}'
                ))
            
            for log_data in meditation_logs:
                await cursor.execute("""
                    INSERT IGNORE INTO logs (goal_id, user_id, date, value, note, created_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                """, log_data)
            
            print(f"✅ Created {len(meditation_logs)} meditation log entries for Goal C")
            
            await conn.commit()
            print("\n🎉 Demo data created successfully!")
            print("📧 Demo user: demo@local.test")
            print("🔑 Password: demo123")
            
    except Exception as e:
        print(f"❌ Error creating demo data: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    asyncio.run(create_demo_data())
