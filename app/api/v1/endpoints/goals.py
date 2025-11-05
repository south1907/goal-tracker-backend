"""
Goals endpoints.
"""

from datetime import datetime
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_user
from app.core.database import get_db
from app.models import User
from app.repositories import GoalRepository, LogRepository
from app.schemas import (
    Goal,
    GoalCreate,
    GoalFilters,
    GoalUpdate,
    GoalWithStats,
    Log,
    LogCreate,
    LogFilters,
    LogUpdate,
    PaginatedResponse,
    PaginationParams,
    ProgressStats,
)
from app.services import calculate_progress_stats

router = APIRouter()


@router.post("", response_model=Goal, status_code=status.HTTP_201_CREATED)
async def create_goal_no_slash(
    goal_data: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new goal (no trailing slash)."""
    goal_repo = GoalRepository(db)
    
    goal_dict = goal_data.dict()
    goal_dict["owner_id"] = current_user.id
    goal_dict["status"] = "active"
    
    goal = await goal_repo.create(goal_dict)
    return Goal.from_orm(goal)


@router.post("/", response_model=Goal, status_code=status.HTTP_201_CREATED)
async def create_goal(
    goal_data: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new goal."""
    goal_repo = GoalRepository(db)
    
    goal_dict = goal_data.dict()
    goal_dict["owner_id"] = current_user.id
    goal_dict["status"] = "active"
    
    goal = await goal_repo.create(goal_dict)
    return Goal.from_orm(goal)


@router.get("", response_model=PaginatedResponse)
async def list_goals_no_slash(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query(None, regex="^(draft|active|ended)$"),
    goal_type: str = Query(None, regex="^(count|sum|streak|milestone|open)$"),
    privacy: str = Query(None, regex="^(public|unlisted|private)$"),
    q: str = Query(None, min_length=1, max_length=100),
    include_stats: bool = Query(False, description="Include progress statistics in response"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's goals with filtering and pagination (no trailing slash)."""
    goal_repo = GoalRepository(db)
    log_repo = LogRepository(db)
    
    filters = GoalFilters(
        status=status,
        goal_type=goal_type,
        privacy=privacy,
        q=q,
    )
    
    pagination = PaginationParams(page=page, page_size=page_size)
    
    goals, total = await goal_repo.get_by_owner(
        current_user.id,
        filters=filters,
        pagination=pagination,
    )
    
    # If include_stats is True, calculate progress for all goals
    if include_stats:
        # Get all logs for user's goals efficiently
        goal_ids = [goal.id for goal in goals]
        all_logs = await log_repo.get_by_user_and_goals(current_user.id, goal_ids)
        
        # Group logs by goal_id
        logs_by_goal = {}
        for log in all_logs:
            if log.goal_id not in logs_by_goal:
                logs_by_goal[log.goal_id] = []
            logs_by_goal[log.goal_id].append(log)
        
        # Convert to GoalWithStats schemas with progress
        goal_schemas = []
        for goal in goals:
            goal_logs = logs_by_goal.get(goal.id, [])
            stats = calculate_progress_stats(goal, goal_logs)
            
            goal_dict = Goal.from_orm(goal).dict()
            goal_dict.update({
                "progress_pct": stats.progress_pct,
                "achieved": stats.achieved,
                "achieved_value": stats.achieved_value,
                "required_pace": stats.required_pace,
                "actual_pace": stats.actual_pace,
                "streak": stats.streak,
            })
            goal_schemas.append(GoalWithStats(**goal_dict))
    else:
        # Convert SQLAlchemy models to Pydantic schemas
        goal_schemas = [Goal.from_orm(goal) for goal in goals]
    
    pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(
        items=goal_schemas,
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
    )


@router.get("/", response_model=PaginatedResponse)
async def list_goals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query(None, regex="^(draft|active|ended)$"),
    goal_type: str = Query(None, regex="^(count|sum|streak|milestone|open)$"),
    privacy: str = Query(None, regex="^(public|unlisted|private)$"),
    q: str = Query(None, min_length=1, max_length=100),
    include_stats: bool = Query(False, description="Include progress statistics in response"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's goals with filtering and pagination."""
    goal_repo = GoalRepository(db)
    log_repo = LogRepository(db)
    
    filters = GoalFilters(
        status=status,
        goal_type=goal_type,
        privacy=privacy,
        q=q,
    )
    
    pagination = PaginationParams(page=page, page_size=page_size)
    
    goals, total = await goal_repo.get_by_owner(
        current_user.id,
        filters=filters,
        pagination=pagination,
    )
    
    # If include_stats is True, calculate progress for all goals
    if include_stats:
        # Get all logs for user's goals efficiently
        goal_ids = [goal.id for goal in goals]
        all_logs = await log_repo.get_by_user_and_goals(current_user.id, goal_ids)
        
        # Group logs by goal_id
        logs_by_goal = {}
        for log in all_logs:
            if log.goal_id not in logs_by_goal:
                logs_by_goal[log.goal_id] = []
            logs_by_goal[log.goal_id].append(log)
        
        # Convert to GoalWithStats schemas with progress
        goal_schemas = []
        for goal in goals:
            goal_logs = logs_by_goal.get(goal.id, [])
            stats = calculate_progress_stats(goal, goal_logs)
            
            goal_dict = Goal.from_orm(goal).dict()
            goal_dict.update({
                "progress_pct": stats.progress_pct,
                "achieved": stats.achieved,
                "achieved_value": stats.achieved_value,
                "required_pace": stats.required_pace,
                "actual_pace": stats.actual_pace,
                "streak": stats.streak,
            })
            goal_schemas.append(GoalWithStats(**goal_dict))
    else:
        # Convert SQLAlchemy models to Pydantic schemas
        goal_schemas = [Goal.from_orm(goal) for goal in goals]
    
    pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(
        items=goal_schemas,
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
    )


@router.get("/public", response_model=PaginatedResponse)
async def list_public_goals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List public goals."""
    goal_repo = GoalRepository(db)
    
    pagination = PaginationParams(page=page, page_size=page_size)
    
    goals, total = await goal_repo.get_public_goals(pagination=pagination)
    
    pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(
        items=goals,
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
    )


@router.get("/{goal_id}", response_model=Goal)
async def get_goal(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific goal."""
    goal_repo = GoalRepository(db)
    
    goal = await goal_repo.get_by_id(goal_id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )
    
    # Check privacy
    if goal.privacy == "private" and goal.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    return Goal.from_orm(goal)


@router.get("/share/{share_token}", response_model=Goal)
async def get_goal_by_share_token(
    share_token: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a goal by share token (public access, no auth required)."""
    goal_repo = GoalRepository(db)
    
    goal = await goal_repo.get_by_share_token(share_token)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )
    
    # Only allow access to public or unlisted goals
    if goal.privacy == "private":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This goal is private and cannot be shared",
        )
    
    return Goal.from_orm(goal)


@router.get("/share/{share_token}/logs", response_model=PaginatedResponse)
async def get_shared_goal_logs(
    share_token: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get logs for a shared goal (public access, no auth required)."""
    goal_repo = GoalRepository(db)
    log_repo = LogRepository(db)
    
    goal = await goal_repo.get_by_share_token(share_token)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )
    
    # Only allow access to public or unlisted goals
    if goal.privacy == "private":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This goal is private and cannot be shared",
        )
    
    # Get logs for the goal
    pagination = PaginationParams(page=page, page_size=page_size)
    logs, total = await log_repo.get_by_goal(goal.id, pagination=pagination)
    
    log_schemas = [Log.from_orm(log) for log in logs]
    pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(
        items=log_schemas,
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
    )


@router.get("/share/{share_token}/progress", response_model=ProgressStats)
async def get_shared_goal_progress(
    share_token: str,
    window: str = Query("all", regex="^(all|week|month)$"),
    db: AsyncSession = Depends(get_db),
):
    """Get progress stats for a shared goal (public access, no auth required)."""
    goal_repo = GoalRepository(db)
    log_repo = LogRepository(db)
    
    goal = await goal_repo.get_by_share_token(share_token)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )
    
    # Only allow access to public or unlisted goals
    if goal.privacy == "private":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This goal is private and cannot be shared",
        )
    
    # Get all logs for the goal to calculate stats
    logs, _ = await log_repo.get_by_goal(goal.id, pagination=None)
    
    # Calculate progress stats (window parameter is not used in current implementation)
    stats = calculate_progress_stats(goal, logs)
    
    return stats


@router.post("/{goal_id}/generate-share-token", response_model=dict)
async def generate_share_token(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate or regenerate share token for a goal."""
    goal_repo = GoalRepository(db)
    
    goal = await goal_repo.get_by_id(goal_id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )
    
    # Only owner can generate share token
    if goal.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the goal owner can generate share tokens",
        )
    
    share_token = await goal_repo.generate_share_token(goal_id)
    
    return {"share_token": share_token}


@router.patch("/{goal_id}", response_model=Goal)
async def update_goal(
    goal_id: int,
    goal_data: GoalUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a goal."""
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
    
    # Update goal
    update_dict = goal_data.dict(exclude_unset=True)
    goal = await goal_repo.update(goal, update_dict)
    
    return goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a goal."""
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
    
    try:
        await goal_repo.delete(goal)
    except Exception as e:
        await db.rollback()
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error deleting goal {goal_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete goal: {str(e)}",
        )


@router.get("/{goal_id}/progress", response_model=ProgressStats)
async def get_goal_progress(
    goal_id: int,
    window: str = Query("last_30d", regex="^(last_30d|cycle)$"),
    tz: str = Query("Asia/Bangkok"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get goal progress statistics."""
    goal_repo = GoalRepository(db)
    log_repo = LogRepository(db)
    
    goal = await goal_repo.get_by_id(goal_id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )
    
    # Check access
    if goal.privacy == "private" and goal.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    # Get logs
    logs = await log_repo.get_by_user_and_goal(current_user.id, goal_id)
    
    # Calculate progress stats
    stats = calculate_progress_stats(goal, logs)
    
    return stats


@router.get("/{goal_id}/chart", response_model=List[dict])
async def get_goal_chart(
    goal_id: int,
    bucket: str = Query("daily", regex="^(daily|weekly)$"),
    from_date: str = Query(...),
    to_date: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get goal chart data."""
    from datetime import datetime
    
    goal_repo = GoalRepository(db)
    log_repo = LogRepository(db)
    
    goal = await goal_repo.get_by_id(goal_id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )
    
    # Check access
    if goal.privacy == "private" and goal.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    # Parse dates
    try:
        from_dt = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
        to_dt = datetime.fromisoformat(to_date.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format",
        )
    
    # Get chart data
    logs = await log_repo.get_chart_data(goal_id, from_dt, to_dt)
    
    # Process data for chart
    chart_data = []
    cumulative = 0
    
    for log in logs:
        cumulative += float(log.value)
        chart_data.append({
            "date": log.date.isoformat(),
            "value": float(log.value),
            "cumulative": cumulative,
        })
    
    return chart_data


@router.get("/{goal_id}/heatmap", response_model=List[dict])
async def get_goal_heatmap(
    goal_id: int,
    month: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get goal heatmap data for a specific month."""
    from datetime import datetime
    
    goal_repo = GoalRepository(db)
    log_repo = LogRepository(db)
    
    goal = await goal_repo.get_by_id(goal_id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )
    
    # Check access
    if goal.privacy == "private" and goal.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    # Parse month
    try:
        month_dt = datetime.fromisoformat(month + "-01T00:00:00+00:00")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid month format",
        )
    
    # Get heatmap data
    logs = await log_repo.get_heatmap_data(goal_id, month_dt)
    
    # Process data for heatmap
    heatmap_data = []
    logs_by_date = {}
    
    for log in logs:
        date_key = log.date.date().isoformat()
        if date_key not in logs_by_date:
            logs_by_date[date_key] = 0
        logs_by_date[date_key] += float(log.value)
    
    for date_str, value in logs_by_date.items():
        # Calculate intensity (0-4)
        intensity = min(4, max(0, int(value)))
        heatmap_data.append({
            "date": date_str,
            "value": value,
            "intensity": intensity,
        })
    
    return heatmap_data


# Logs endpoints
@router.post("/{goal_id}/logs", response_model=Log, status_code=status.HTTP_201_CREATED)
async def create_log(
    goal_id: int,
    log_data: LogCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new log entry for a goal."""
    goal_repo = GoalRepository(db)
    log_repo = LogRepository(db)
    
    # Check if goal exists and user has access
    goal = await goal_repo.get_by_id(goal_id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )
    
    # Check access
    if goal.privacy == "private" and goal.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    # Create log
    log_dict = log_data.dict()
    log_dict["goal_id"] = goal_id
    log_dict["user_id"] = current_user.id
    
    # Set date if not provided
    if not log_dict.get("date"):
        log_dict["date"] = datetime.utcnow()
    
    log = await log_repo.create(log_dict)
    return Log.from_orm(log)


@router.get("/{goal_id}/logs", response_model=PaginatedResponse)
async def list_goal_logs(
    goal_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    from_date: str = Query(None),
    to_date: str = Query(None),
    order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List logs for a specific goal."""
    goal_repo = GoalRepository(db)
    log_repo = LogRepository(db)
    
    # Check if goal exists and user has access
    goal = await goal_repo.get_by_id(goal_id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )
    
    # Check access
    if goal.privacy == "private" and goal.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    # Build filters
    filters = LogFilters(
        from_date=from_date,
        to_date=to_date,
        order=order,
    )
    
    pagination = PaginationParams(page=page, page_size=page_size)
    
    logs, total = await log_repo.get_by_goal(
        goal_id,
        filters=filters,
        pagination=pagination,
    )
    
    # Convert SQLAlchemy models to Pydantic schemas
    log_schemas = [Log.from_orm(log) for log in logs]
    
    pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(
        items=log_schemas,
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
    )


@router.patch("/logs/{log_id}", response_model=Log)
async def update_log(
    log_id: int,
    log_data: LogUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a log entry."""
    log_repo = LogRepository(db)
    
    # Get log
    log = await log_repo.get_by_id(log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log not found",
        )
    
    # Check ownership
    if log.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    # Update log
    update_dict = log_data.dict(exclude_unset=True)
    log = await log_repo.update(log, update_dict)
    return Log.from_orm(log)


@router.delete("/logs/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_log(
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a log entry."""
    log_repo = LogRepository(db)
    
    # Get log
    log = await log_repo.get_by_id(log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log not found",
        )
    
    # Check ownership
    if log.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    # Delete log
    await log_repo.delete(log)
