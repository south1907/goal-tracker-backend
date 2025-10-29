"""
Statistics endpoints.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.v1.endpoints.auth import get_current_user
from app.core.database import get_db
from app.models import Goal, Log, User
from app.repositories import GoalRepository, LogRepository
from app.schemas import OverviewStats

router = APIRouter()


@router.get("/overview", response_model=OverviewStats)
async def get_overview_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get overview statistics across all user's goals."""
    goal_repo = GoalRepository(db)
    log_repo = LogRepository(db)
    
    # Get user's goals
    goals, _ = await goal_repo.get_by_owner(current_user.id)
    
    if not goals:
        return OverviewStats(
            total_goals=0,
            active_goals=0,
            completed_goals=0,
            total_logs=0,
            best_day=None,
            best_week=None,
            longest_streak=0,
            completion_rate=0.0,
        )
    
    # Calculate basic stats
    total_goals = len(goals)
    active_goals = len([g for g in goals if g.status == "active"])
    completed_goals = len([g for g in goals if g.status == "ended"])
    
    # Get total logs count
    total_logs_query = select(func.count(Log.id)).where(Log.user_id == current_user.id)
    total_logs_result = await db.execute(total_logs_query)
    total_logs = total_logs_result.scalar() or 0
    
    # Calculate best day and week
    best_day = None
    best_week = None
    longest_streak = 0
    
    # Get logs grouped by date
    logs_query = (
        select(Log.date, func.sum(Log.value).label("daily_total"))
        .where(Log.user_id == current_user.id)
        .group_by(Log.date)
        .order_by(func.sum(Log.value).desc())
    )
    
    logs_result = await db.execute(logs_query)
    daily_totals = logs_result.fetchall()
    
    if daily_totals:
        best_day = daily_totals[0][0]
        
        # Calculate weekly totals
        weekly_totals = {}
        for date, total in daily_totals:
            week_start = date - timedelta(days=date.weekday())
            week_key = week_start.date()
            if week_key not in weekly_totals:
                weekly_totals[week_key] = 0
            weekly_totals[week_key] += float(total)
        
        if weekly_totals:
            best_week_date = max(weekly_totals.keys(), key=lambda k: weekly_totals[k])
            best_week = datetime.combine(best_week_date, datetime.min.time())
    
    # Calculate longest streak across all streak goals
    streak_goals = [g for g in goals if g.goal_type == "streak"]
    for goal in streak_goals:
        logs = await log_repo.get_by_user_and_goal(current_user.id, goal.id)
        
        # Calculate streak for this goal
        current_streak = 0
        max_streak = 0
        
        # Sort logs by date
        sorted_logs = sorted(logs, key=lambda x: x.date)
        
        # Group by date
        logs_by_date = {}
        for log in sorted_logs:
            date_key = log.date.date()
            if date_key not in logs_by_date:
                logs_by_date[date_key] = []
            logs_by_date[date_key].append(log)
        
        # Calculate streak
        current_date = goal.start_at.date()
        end_date = datetime.utcnow().date()
        
        while current_date <= end_date:
            if current_date in logs_by_date:
                has_activity = any(log.value > 0 for log in logs_by_date[current_date])
                if has_activity:
                    current_streak += 1
                    max_streak = max(max_streak, current_streak)
                else:
                    current_streak = 0
            else:
                current_streak = 0
            
            current_date += timedelta(days=1)
        
        longest_streak = max(longest_streak, max_streak)
    
    # Calculate completion rate
    completion_rate = (completed_goals / total_goals * 100) if total_goals > 0 else 0.0
    
    return OverviewStats(
        total_goals=total_goals,
        active_goals=active_goals,
        completed_goals=completed_goals,
        total_logs=total_logs,
        best_day=best_day,
        best_week=best_week,
        longest_streak=longest_streak,
        completion_rate=completion_rate,
    )


@router.get("/goals/{goal_id}/cycle/close", status_code=status.HTTP_204_NO_CONTENT)
async def close_goal_cycle(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Close current cycle and create cycle summary (optional feature)."""
    goal_repo = GoalRepository(db)
    
    goal = await goal_repo.get_by_id(goal_id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )
    
    # Check ownership
    if goal.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    # This is a placeholder for cycle closing functionality
    # In a full implementation, this would:
    # 1. Calculate cycle statistics
    # 2. Create a CycleSummary record
    # 3. Reset or advance the cycle
    
    # For now, just return success
    pass
