#!/usr/bin/env python3
"""
Script to clear all test data from the database.
This will delete all logs, goals, and optionally all users.
"""

import asyncio
from sqlalchemy import delete, select

from app.core.database import async_session_factory
from app.models import Log, Goal, User


async def clear_all_test_data(delete_users: bool = False):
    """Clear all test data from the database."""
    async with async_session_factory() as session:
        try:
            print("🗑️  Starting to clear test data...")
            
            # Delete all logs
            result = await session.execute(select(Log))
            logs = result.scalars().all()
            log_count = len(logs)
            if logs:
                await session.execute(delete(Log))
                print(f"✅ Deleted {log_count} log entries")
            else:
                print("ℹ️  No logs to delete")
            
            # Delete all goals
            result = await session.execute(select(Goal))
            goals = result.scalars().all()
            goal_count = len(goals)
            if goals:
                await session.execute(delete(Goal))
                print(f"✅ Deleted {goal_count} goals")
            else:
                print("ℹ️  No goals to delete")
            
            # Optionally delete all users (except if you want to keep them)
            if delete_users:
                result = await session.execute(select(User))
                users = result.scalars().all()
                user_count = len(users)
                if users:
                    await session.execute(delete(User))
                    print(f"✅ Deleted {user_count} users")
                else:
                    print("ℹ️  No users to delete")
            else:
                result = await session.execute(select(User))
                users = result.scalars().all()
                print(f"ℹ️  Keeping {len(users)} users (use --delete-users to delete them)")
            
            # Commit the changes
            await session.commit()
            
            print("\n✅ All test data cleared successfully!")
            print(f"   - Deleted {log_count} logs")
            print(f"   - Deleted {goal_count} goals")
            if delete_users:
                print(f"   - Deleted {len(users)} users")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error clearing test data: {e}")
            raise


async def clear_specific_user_data(email: str):
    """Clear all data for a specific user."""
    async with async_session_factory() as session:
        try:
            print(f"🗑️  Starting to clear data for user: {email}")
            
            # Find user
            result = await session.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"❌ User with email '{email}' not found")
                return
            
            user_id = user.id
            print(f"✅ Found user: {user.display_name} (ID: {user_id})")
            
            # Delete all logs for this user
            result = await session.execute(
                select(Log).where(Log.user_id == user_id)
            )
            logs = result.scalars().all()
            log_count = len(logs)
            if logs:
                await session.execute(delete(Log).where(Log.user_id == user_id))
                print(f"✅ Deleted {log_count} log entries")
            else:
                print("ℹ️  No logs to delete")
            
            # Delete all goals for this user
            result = await session.execute(
                select(Goal).where(Goal.owner_id == user_id)
            )
            goals = result.scalars().all()
            goal_count = len(goals)
            if goals:
                await session.execute(delete(Goal).where(Goal.owner_id == user_id))
                print(f"✅ Deleted {goal_count} goals")
            else:
                print("ℹ️  No goals to delete")
            
            # Commit the changes
            await session.commit()
            
            print("\n✅ All data cleared for user successfully!")
            print(f"   - Deleted {log_count} logs")
            print(f"   - Deleted {goal_count} goals")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error clearing user data: {e}")
            raise


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--delete-users":
            asyncio.run(clear_all_test_data(delete_users=True))
        elif sys.argv[1] == "--user" and len(sys.argv) > 2:
            email = sys.argv[2]
            asyncio.run(clear_specific_user_data(email))
        elif sys.argv[1] == "--help":
            print("Usage:")
            print("  python clear_test_data.py                    # Clear all logs and goals (keep users)")
            print("  python clear_test_data.py --delete-users     # Clear all logs, goals, and users")
            print("  python clear_test_data.py --user <email>     # Clear data for specific user")
            print("  python clear_test_data.py --help             # Show this help")
        else:
            print("Unknown option. Use --help for usage information.")
    else:
        # Default: clear all logs and goals but keep users
        asyncio.run(clear_all_test_data(delete_users=False))

