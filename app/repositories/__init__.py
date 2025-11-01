"""
Repository layer for data access patterns.
"""

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_, delete, desc, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import CycleSummary, Goal, GoalMember, Log, User
from app.schemas import GoalFilters, LogFilters, PaginationParams


class UserRepository:
    """User repository for database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, user_data: dict) -> User:
        """Create a new user."""
        user = User(**user_data)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    async def update(self, user: User, update_data: dict) -> User:
        """Update user."""
        for field, value in update_data.items():
            setattr(user, field, value)
        await self.db.commit()
        await self.db.refresh(user)
        return user


class GoalRepository:
    """Goal repository for database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, goal_data: dict) -> Goal:
        """Create a new goal."""
        goal = Goal(**goal_data)
        self.db.add(goal)
        await self.db.commit()
        await self.db.refresh(goal)
        return goal
    
    async def get_by_id(self, goal_id: int) -> Optional[Goal]:
        """Get goal by ID."""
        result = await self.db.execute(
            select(Goal)
            .where(Goal.id == goal_id)
            .options(
                # Eager load relationships to avoid N+1 queries
                # Note: SQLAlchemy 2.x syntax
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_owner(self, owner_id: int, filters: Optional[GoalFilters] = None, 
                          pagination: Optional[PaginationParams] = None) -> tuple[List[Goal], int]:
        """Get goals by owner with filtering and pagination."""
        query = select(Goal).where(Goal.owner_id == owner_id)
        
        # Apply filters
        if filters:
            if filters.status:
                query = query.where(Goal.status == filters.status)
            if filters.goal_type:
                query = query.where(Goal.goal_type == filters.goal_type)
            if filters.privacy:
                query = query.where(Goal.privacy == filters.privacy)
            if filters.q:
                search_term = f"%{filters.q}%"
                query = query.where(
                    or_(
                        Goal.name.ilike(search_term),
                        Goal.description.ilike(search_term)
                    )
                )
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # Apply pagination
        if pagination:
            offset = (pagination.page - 1) * pagination.page_size
            query = query.offset(offset).limit(pagination.page_size)
        
        # Order by created_at desc
        query = query.order_by(desc(Goal.created_at))
        
        result = await self.db.execute(query)
        goals = result.scalars().all()
        
        return list(goals), total
    
    async def update(self, goal: Goal, update_data: dict) -> Goal:
        """Update goal."""
        for field, value in update_data.items():
            setattr(goal, field, value)
        await self.db.commit()
        await self.db.refresh(goal)
        return goal
    
    async def delete(self, goal: Goal) -> None:
        """Delete goal permanently (hard delete)."""
        try:
            # First delete all related logs
            await self.db.execute(
                delete(Log).where(Log.goal_id == goal.id)
            )
            
            # Delete goal members
            await self.db.execute(
                delete(GoalMember).where(GoalMember.goal_id == goal.id)
            )
            
            # Delete cycle summaries if they exist
            await self.db.execute(
                delete(CycleSummary).where(CycleSummary.goal_id == goal.id)
            )
            
            # Finally delete the goal itself
            await self.db.execute(
                delete(Goal).where(Goal.id == goal.id)
            )
            
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise e
    
    async def get_public_goals(self, pagination: Optional[PaginationParams] = None) -> tuple[List[Goal], int]:
        """Get public goals."""
        query = select(Goal).where(Goal.privacy == "public")
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # Apply pagination
        if pagination:
            offset = (pagination.page - 1) * pagination.page_size
            query = query.offset(offset).limit(pagination.page_size)
        
        query = query.order_by(desc(Goal.created_at))
        
        result = await self.db.execute(query)
        goals = result.scalars().all()
        
        return list(goals), total


class LogRepository:
    """Log repository for database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, log_data: dict) -> Log:
        """Create a new log entry."""
        log = Log(**log_data)
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log
    
    async def get_by_id(self, log_id: int) -> Optional[Log]:
        """Get log by ID."""
        result = await self.db.execute(select(Log).where(Log.id == log_id))
        return result.scalar_one_or_none()
    
    async def get_by_goal(self, goal_id: int, filters: Optional[LogFilters] = None,
                         pagination: Optional[PaginationParams] = None) -> tuple[List[Log], int]:
        """Get logs by goal with filtering and pagination."""
        query = select(Log).where(Log.goal_id == goal_id)
        
        # Apply filters
        if filters:
            if filters.from_date:
                query = query.where(Log.date >= filters.from_date)
            if filters.to_date:
                query = query.where(Log.date <= filters.to_date)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # Apply pagination
        if pagination:
            offset = (pagination.page - 1) * pagination.page_size
            query = query.offset(offset).limit(pagination.page_size)
        
        # Apply ordering
        order = desc(Log.date) if filters and filters.order == "desc" else Log.date
        query = query.order_by(order)
        
        result = await self.db.execute(query)
        logs = result.scalars().all()
        
        return list(logs), total
    
    async def get_by_user_and_goal(self, user_id: int, goal_id: int) -> List[Log]:
        """Get logs by user and goal."""
        result = await self.db.execute(
            select(Log)
            .where(and_(Log.user_id == user_id, Log.goal_id == goal_id))
            .order_by(Log.date)
        )
        return list(result.scalars().all())
    
    async def get_by_user_and_goals(self, user_id: int, goal_ids: List[int]) -> List[Log]:
        """Get logs by user and multiple goals."""
        if not goal_ids:
            return []
        result = await self.db.execute(
            select(Log)
            .where(and_(Log.user_id == user_id, Log.goal_id.in_(goal_ids)))
            .order_by(Log.date)
        )
        return list(result.scalars().all())
    
    async def update(self, log: Log, update_data: dict) -> Log:
        """Update log entry."""
        for field, value in update_data.items():
            setattr(log, field, value)
        await self.db.commit()
        await self.db.refresh(log)
        return log
    
    async def delete(self, log: Log) -> None:
        """Delete log entry."""
        await self.db.delete(log)
        await self.db.commit()
    
    async def get_chart_data(self, goal_id: int, from_date: datetime, to_date: datetime) -> List[Log]:
        """Get logs for chart data within date range."""
        result = await self.db.execute(
            select(Log)
            .where(
                and_(
                    Log.goal_id == goal_id,
                    Log.date >= from_date,
                    Log.date <= to_date
                )
            )
            .order_by(Log.date)
        )
        return list(result.scalars().all())
    
    async def get_heatmap_data(self, goal_id: int, month: datetime) -> List[Log]:
        """Get logs for heatmap data for a specific month."""
        # Calculate month start and end
        month_start = month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if month.month == 12:
            month_end = month.replace(year=month.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = month.replace(month=month.month + 1, day=1) - timedelta(days=1)
        
        result = await self.db.execute(
            select(Log)
            .where(
                and_(
                    Log.goal_id == goal_id,
                    Log.date >= month_start,
                    Log.date <= month_end
                )
            )
            .order_by(Log.date)
        )
        return list(result.scalars().all())
