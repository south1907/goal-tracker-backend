"""
Logs endpoints.
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_user
from app.core.database import get_db
from app.models import User
from app.repositories import GoalRepository, LogRepository
from app.schemas import (
    Log,
    LogCreate,
    LogFilters,
    LogUpdate,
    PaginatedResponse,
    PaginationParams,
)

router = APIRouter()


@router.post("/goals/{goal_id}/logs", response_model=Log, status_code=status.HTTP_201_CREATED)
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
    return log


@router.get("/goals/{goal_id}/logs", response_model=PaginatedResponse)
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
    
    # Parse date filters
    filters = LogFilters(order=order)
    if from_date:
        try:
            filters.from_date = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid from_date format",
            )
    
    if to_date:
        try:
            filters.to_date = datetime.fromisoformat(to_date.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid to_date format",
            )
    
    pagination = PaginationParams(page=page, page_size=page_size)
    
    logs, total = await log_repo.get_by_goal(
        goal_id,
        filters=filters,
        pagination=pagination,
    )
    
    pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(
        items=logs,
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
    )


@router.get("/all", response_model=PaginatedResponse)
async def get_all_user_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(1000, ge=1, le=10000),
    from_date: str = Query(None),
    to_date: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all logs for the current user across all goals."""
    log_repo = LogRepository(db)
    
    # Parse date filters
    filters = LogFilters(order="desc")
    if from_date:
        try:
            filters.from_date = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid from_date format",
            )
    
    if to_date:
        try:
            filters.to_date = datetime.fromisoformat(to_date.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid to_date format",
            )
    
    # Get all logs for user (get all goals owned by user first)
    goal_repo = GoalRepository(db)
    user_goals, _ = await goal_repo.get_by_owner(current_user.id)
    goal_ids = [goal.id for goal in user_goals]
    
    if not goal_ids:
        pages = 0
        return PaginatedResponse(
            items=[],
            page=page,
            page_size=page_size,
            total=0,
            pages=pages,
        )
    
    # Get logs across all user's goals
    all_logs = await log_repo.get_by_user_and_goals(current_user.id, goal_ids)
    
    # Apply date filters manually since get_by_user_and_goals doesn't support filters
    filtered_logs = all_logs
    if filters.from_date:
        filtered_logs = [log for log in filtered_logs if log.date >= filters.from_date]
    if filters.to_date:
        filtered_logs = [log for log in filtered_logs if log.date <= filters.to_date]
    
    # Sort
    if filters.order == "desc":
        filtered_logs.sort(key=lambda x: x.date, reverse=True)
    else:
        filtered_logs.sort(key=lambda x: x.date)
    
    # Paginate
    total = len(filtered_logs)
    pages = (total + page_size - 1) // page_size
    offset = (page - 1) * page_size
    paginated_logs = filtered_logs[offset:offset + page_size]
    
    return PaginatedResponse(
        items=[Log.from_orm(log) for log in paginated_logs],
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
    )


@router.get("/{log_id}", response_model=Log)
async def get_log(
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific log entry."""
    log_repo = LogRepository(db)
    goal_repo = GoalRepository(db)
    
    log = await log_repo.get_by_id(log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log not found",
        )
    
    # Check access through goal
    goal = await goal_repo.get_by_id(log.goal_id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )
    
    if goal.privacy == "private" and goal.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    return log


@router.patch("/{log_id}", response_model=Log)
async def update_log(
    log_id: int,
    log_data: LogUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a log entry."""
    log_repo = LogRepository(db)
    goal_repo = GoalRepository(db)
    
    log = await log_repo.get_by_id(log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log not found",
        )
    
    # Check access - user must be the creator or goal owner
    goal = await goal_repo.get_by_id(log.goal_id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )
    
    if log.user_id != current_user.id and goal.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    # Update log
    update_dict = log_data.dict(exclude_unset=True)
    log = await log_repo.update(log, update_dict)
    
    return log


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_log(
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a log entry."""
    log_repo = LogRepository(db)
    goal_repo = GoalRepository(db)
    
    log = await log_repo.get_by_id(log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log not found",
        )
    
    # Check access - user must be the creator or goal owner
    goal = await goal_repo.get_by_id(log.goal_id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )
    
    if log.user_id != current_user.id and goal.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    await log_repo.delete(log)
