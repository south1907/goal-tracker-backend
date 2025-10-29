"""
Seed data utility for development.
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.core.security import get_password_hash
from app.models import Goal, Log, User
from app.repositories import GoalRepository, LogRepository, UserRepository


async def create_seed_data():
    """Create seed data for development."""
    
    async with async_session_factory() as db:
        user_repo = UserRepository(db)
        goal_repo = GoalRepository(db)
        log_repo = LogRepository(db)
        
        # Create demo user
        demo_user = await user_repo.get_by_email("demo@local.test")
        if not demo_user:
            demo_user = await user_repo.create({
                "email": "demo@local.test",
                "password_hash": get_password_hash("demo123"),
                "display_name": "Demo User",
            })
            print(f"Created demo user: {demo_user.email}")
        else:
            print(f"Demo user already exists: {demo_user.email}")
        
        # Create Goal A: Read 20 Books in 2025
        goal_a = await goal_repo.create({
            "owner_id": demo_user.id,
            "name": "Read 20 Books in 2025",
            "description": "Read 20 books throughout the year 2025",
            "emoji": "📚",
            "goal_type": "count",
            "unit": "books",
            "target": Decimal("20"),
            "timeframe_type": "fixed",
            "start_at": datetime(2025, 1, 1, 0, 0, 0),
            "end_at": datetime(2025, 12, 31, 23, 59, 59),
            "privacy": "private",
            "status": "active",
            "settings_json": {
                "milestones": [
                    {"label": "25%", "threshold": 25},
                    {"label": "50%", "threshold": 50},
                    {"label": "75%", "threshold": 75},
                    {"label": "100%", "threshold": 100},
                ]
            }
        })
        print(f"Created Goal A: {goal_a.name}")
        
        # Create Goal B: Run 200 km in October
        goal_b = await goal_repo.create({
            "owner_id": demo_user.id,
            "name": "Run 200 km in October",
            "description": "Run 200 kilometers during October 2025",
            "emoji": "🏃",
            "goal_type": "sum",
            "unit": "km",
            "target": Decimal("200"),
            "timeframe_type": "fixed",
            "start_at": datetime(2025, 10, 1, 0, 0, 0),
            "end_at": datetime(2025, 10, 31, 23, 59, 59),
            "privacy": "private",
            "status": "active",
            "settings_json": {
                "milestones": [
                    {"label": "50 km", "threshold": 25},
                    {"label": "100 km", "threshold": 50},
                    {"label": "150 km", "threshold": 75},
                    {"label": "200 km", "threshold": 100},
                ]
            }
        })
        print(f"Created Goal B: {goal_b.name}")
        
        # Create Goal C: Daily Meditation Streak
        goal_c = await goal_repo.create({
            "owner_id": demo_user.id,
            "name": "Daily Meditation Streak",
            "description": "Meditate every day for at least 10 minutes",
            "emoji": "🧘",
            "goal_type": "streak",
            "unit": "days",
            "target": Decimal("30"),
            "timeframe_type": "rolling",
            "start_at": datetime.utcnow() - timedelta(days=30),
            "rolling_days": 30,
            "privacy": "private",
            "status": "active",
            "settings_json": {
                "milestones": [
                    {"label": "7 days", "threshold": 23},
                    {"label": "14 days", "threshold": 47},
                    {"label": "21 days", "threshold": 70},
                    {"label": "30 days", "threshold": 100},
                ]
            }
        })
        print(f"Created Goal C: {goal_c.name}")
        
        # Create logs for Goal B (Run 200 km)
        logs_data = [
            {
                "goal_id": goal_b.id,
                "user_id": demo_user.id,
                "date": datetime(2025, 10, 3, 10, 0, 0),
                "value": Decimal("10"),
                "note": "Morning run in the park",
            },
            {
                "goal_id": goal_b.id,
                "user_id": demo_user.id,
                "date": datetime(2025, 10, 7, 8, 0, 0),
                "value": Decimal("12"),
                "note": "Long run along the river",
            },
            {
                "goal_id": goal_b.id,
                "user_id": demo_user.id,
                "date": datetime(2025, 10, 10, 18, 0, 0),
                "value": Decimal("8"),
                "note": "Evening jog after work",
            },
        ]
        
        for log_data in logs_data:
            log = await log_repo.create(log_data)
            print(f"Created log: {log.value} km on {log.date.date()}")
        
        # Create logs for Goal C (Meditation streak)
        meditation_logs = []
        start_date = datetime.utcnow() - timedelta(days=15)
        
        for i in range(15):  # 15 days of meditation
            log_date = start_date + timedelta(days=i)
            meditation_logs.append({
                "goal_id": goal_c.id,
                "user_id": demo_user.id,
                "date": log_date,
                "value": Decimal("1"),
                "note": f"Meditation session - Day {i+1}",
            })
        
        for log_data in meditation_logs:
            log = await log_repo.create(log_data)
            print(f"Created meditation log: Day {log_data['note'].split()[-1]}")
        
        print("\n✅ Seed data created successfully!")
        print(f"Demo user: {demo_user.email} / Demo123!")
        print(f"Created {len([goal_a, goal_b, goal_c])} goals and {len(logs_data) + len(meditation_logs)} log entries")


if __name__ == "__main__":
    asyncio.run(create_seed_data())
