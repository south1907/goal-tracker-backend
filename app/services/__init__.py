"""
Domain services for business logic calculations.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from app.models import Goal, Log
from app.schemas import ProgressStats


def active_window(goal: Goal, now: Optional[datetime] = None) -> Tuple[datetime, datetime]:
    """
    Calculate the active window for a goal based on its timeframe type.
    
    Args:
        goal: The goal to calculate window for
        now: Current time (defaults to UTC now)
        
    Returns:
        Tuple of (start, end) datetime
    """
    if now is None:
        now = datetime.utcnow()
    
    # Ensure now is timezone-aware if goal datetimes are timezone-aware
    if goal.start_at.tzinfo is not None and now.tzinfo is None:
        from datetime import timezone
        now = now.replace(tzinfo=timezone.utc)
    elif goal.start_at.tzinfo is None and now.tzinfo is not None:
        now = now.replace(tzinfo=None)
    
    if goal.timeframe_type == "fixed":
        end = goal.end_at if goal.end_at is not None else now
        # Ensure end is the same timezone as start
        if goal.start_at.tzinfo is not None and end.tzinfo is None:
            from datetime import timezone
            end = end.replace(tzinfo=timezone.utc)
        elif goal.start_at.tzinfo is None and end.tzinfo is not None:
            end = end.replace(tzinfo=None)
        return goal.start_at, end
    
    elif goal.timeframe_type == "rolling":
        days = goal.rolling_days or 30
        end = now
        start = end - timedelta(days=days)
        # Ensure start has same timezone as goal.start_at
        if goal.start_at.tzinfo is not None and start.tzinfo is None:
            from datetime import timezone
            start = start.replace(tzinfo=timezone.utc)
            end = end.replace(tzinfo=timezone.utc)
        elif goal.start_at.tzinfo is None and start.tzinfo is not None:
            start = start.replace(tzinfo=None)
            end = end.replace(tzinfo=None)
        return start, end
    
    elif goal.timeframe_type == "recurring":
        # For recurring goals, calculate current cycle
        # This is a simplified implementation
        cycle_days = goal.rolling_days or 7
        cycles_passed = (now - goal.start_at).days // cycle_days
        cycle_start = goal.start_at + timedelta(days=cycles_passed * cycle_days)
        cycle_end = cycle_start + timedelta(days=cycle_days)
        return cycle_start, cycle_end
    
    return goal.start_at, now


def sum_in_window(goal: Goal, logs: List[Log], window_start: datetime, window_end: datetime) -> Decimal:
    """
    Calculate the sum of log values within a time window.
    
    Args:
        goal: The goal
        logs: List of log entries
        window_start: Window start time
        window_end: Window end time
        
    Returns:
        Sum of log values in the window
    """
    total = Decimal("0")
    
    for log in logs:
        if window_start <= log.date <= window_end:
            total += log.value
    
    return total


def progress_pct(goal: Goal, logs: List[Log], window_start: datetime, window_end: datetime) -> float:
    """
    Calculate progress percentage for a goal.
    
    Args:
        goal: The goal
        logs: List of log entries
        window_start: Window start time
        window_end: Window end time
        
    Returns:
        Progress percentage (0-100)
    """
    if goal.goal_type == "open" or not goal.target:
        return 0.0
    
    achieved = sum_in_window(goal, logs, window_start, window_end)
    
    if goal.target == 0:
        return 100.0 if achieved > 0 else 0.0
    
    progress = float(achieved / goal.target * 100)
    return min(progress, 100.0)


def required_pace(goal: Goal, now: datetime, window_start: datetime, window_end: datetime) -> float:
    """
    Calculate the required pace to achieve the goal.
    
    Args:
        goal: The goal
        now: Current time
        window_start: Window start time
        window_end: Window end time
        
    Returns:
        Required pace (value per day)
    """
    if goal.goal_type == "open" or not goal.target:
        return 0.0
    
    total_days = (window_end - window_start).days
    if total_days <= 0:
        return 0.0
    
    remaining_value = goal.target
    remaining_days = max(1, (window_end - now).days)
    
    return float(remaining_value / remaining_days)


def actual_pace(goal: Goal, logs: List[Log], window_start: datetime, window_end: datetime) -> float:
    """
    Calculate the actual pace based on logged entries.
    
    Args:
        goal: The goal
        logs: List of log entries
        window_start: Window start time
        window_end: Window end time
        
    Returns:
        Actual pace (value per day)
    """
    total_days = (window_end - window_start).days
    if total_days <= 0:
        return 0.0
    
    achieved = sum_in_window(goal, logs, window_start, window_end)
    return float(achieved / total_days)


def compute_streak(goal: Goal, logs: List[Log], window_start: datetime, window_end: datetime) -> Dict[str, int]:
    """
    Compute streak statistics for a goal.
    
    Args:
        goal: The goal
        logs: List of log entries
        window_start: Window start time
        window_end: Window end time
        
    Returns:
        Dictionary with current and best streak
    """
    if goal.goal_type != "streak":
        return {"current": 0, "best": 0}
    
    # Sort logs by date
    sorted_logs = sorted(logs, key=lambda x: x.date)
    
    current_streak = 0
    best_streak = 0
    temp_streak = 0
    
    # Group logs by date
    logs_by_date = {}
    for log in sorted_logs:
        date_key = log.date.date()
        if date_key not in logs_by_date:
            logs_by_date[date_key] = []
        logs_by_date[date_key].append(log)
    
    # Calculate streaks
    current_date = window_start.date()
    end_date = window_end.date()
    
    while current_date <= end_date:
        if current_date in logs_by_date:
            # Check if any log has value > 0 for streak goals
            has_activity = any(log.value > 0 for log in logs_by_date[current_date])
            if has_activity:
                temp_streak += 1
                best_streak = max(best_streak, temp_streak)
            else:
                temp_streak = 0
        else:
            temp_streak = 0
        
        current_date += timedelta(days=1)
    
    # Current streak is the streak ending at the most recent date
    current_streak = temp_streak
    
    return {
        "current": current_streak,
        "best": best_streak
    }


def milestones_reached(goal: Goal, progress_pct: float) -> List[str]:
    """
    Calculate which milestones have been reached.
    
    Args:
        goal: The goal
        progress_pct: Current progress percentage
        
    Returns:
        List of milestone labels that have been reached
    """
    if not goal.settings_json or "milestones" not in goal.settings_json:
        return []
    
    milestones = goal.settings_json.get("milestones", [])
    reached = []
    
    for milestone in milestones:
        threshold = milestone.get("threshold", 0)
        if progress_pct >= threshold:
            reached.append(milestone.get("label", ""))
    
    return reached


def calculate_progress_stats(
    goal: Goal, 
    logs: List[Log], 
    now: Optional[datetime] = None
) -> ProgressStats:
    """
    Calculate comprehensive progress statistics for a goal.
    
    Args:
        goal: The goal
        logs: List of log entries
        now: Current time (defaults to UTC now)
        
    Returns:
        ProgressStats object with all calculated values
    """
    if now is None:
        now = datetime.utcnow()
    
    window_start, window_end = active_window(goal, now)
    
    achieved_value = sum_in_window(goal, logs, window_start, window_end)
    progress_pct_val = progress_pct(goal, logs, window_start, window_end)
    required_pace_val = required_pace(goal, now, window_start, window_end)
    actual_pace_val = actual_pace(goal, logs, window_start, window_end)
    streak_data = compute_streak(goal, logs, window_start, window_end)
    
    return ProgressStats(
        progress_pct=progress_pct_val,
        achieved=progress_pct_val >= 100.0,
        achieved_value=achieved_value,
        target=goal.target or Decimal("0"),
        unit=goal.unit,
        required_pace=required_pace_val,
        actual_pace=actual_pace_val,
        streak=streak_data
    )
