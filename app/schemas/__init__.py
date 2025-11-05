"""
Pydantic schemas for API validation and serialization.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v),
        }


# User Schemas
class UserBase(BaseSchema):
    """Base user schema."""
    email: str = Field(..., min_length=5, max_length=255)
    display_name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseSchema):
    """User update schema."""
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)


class User(UserBase):
    """User response schema."""
    id: int
    created_at: datetime


# Auth Schemas
class LoginRequest(BaseSchema):
    """Login request schema."""
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=1, max_length=100)

class Token(BaseSchema):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseSchema):
    """Token data schema."""
    user_id: Optional[int] = None


class RefreshToken(BaseSchema):
    """Refresh token request schema."""
    refresh_token: str


# Goal Schemas
class GoalBase(BaseSchema):
    """Base goal schema."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    emoji: str = Field(..., min_length=1, max_length=10)
    goal_type: str = Field(..., pattern="^(count|sum|streak|milestone|open)$")
    unit: str = Field(..., min_length=1, max_length=50)
    target: Optional[Decimal] = Field(None, ge=0)
    timeframe_type: str = Field(..., pattern="^(fixed|rolling|recurring)$")
    start_at: datetime
    end_at: Optional[datetime] = None
    rolling_days: Optional[int] = Field(None, ge=1, le=365)
    rrule: Optional[str] = None
    privacy: str = Field(..., pattern="^(public|unlisted|private)$")
    settings_json: Optional[Dict[str, Any]] = None


class GoalCreate(GoalBase):
    """Goal creation schema."""
    pass


class GoalUpdate(BaseSchema):
    """Goal update schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    emoji: Optional[str] = Field(None, min_length=1, max_length=10)
    target: Optional[Decimal] = Field(None, ge=0)
    end_at: Optional[datetime] = None
    privacy: Optional[str] = Field(None, pattern="^(public|unlisted|private)$")
    settings_json: Optional[Dict[str, Any]] = None


class Goal(GoalBase):
    """Goal response schema."""
    id: int
    owner_id: int
    status: str
    share_token: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class GoalWithStats(Goal):
    """Goal with statistics schema."""
    progress_pct: float
    achieved: bool
    achieved_value: Decimal
    required_pace: float
    actual_pace: float
    streak: Dict[str, Any]


# Log Schemas
class LogBase(BaseSchema):
    """Base log schema."""
    value: Decimal = Field(..., ge=0)
    note: Optional[str] = None
    date: Optional[datetime] = None


class LogCreate(LogBase):
    """Log creation schema."""
    pass


class LogUpdate(BaseSchema):
    """Log update schema."""
    value: Optional[Decimal] = Field(None, ge=0)
    note: Optional[str] = None


class Log(LogBase):
    """Log response schema."""
    id: int
    goal_id: int
    user_id: int
    date: datetime
    attachment_url: Optional[str] = None
    created_at: datetime


# Progress Schemas
class ProgressStats(BaseSchema):
    """Progress statistics schema."""
    progress_pct: float = Field(..., ge=0, le=100)
    achieved: bool
    achieved_value: Decimal
    target: Decimal
    unit: str
    required_pace: float
    actual_pace: float
    streak: Dict[str, Any]


class ChartData(BaseSchema):
    """Chart data schema."""
    date: datetime
    value: Decimal
    cumulative: Decimal


class HeatmapData(BaseSchema):
    """Heatmap data schema."""
    date: str
    value: Decimal
    intensity: int


# Stats Schemas
class OverviewStats(BaseSchema):
    """Overview statistics schema."""
    total_goals: int
    active_goals: int
    completed_goals: int
    total_logs: int
    best_day: Optional[datetime]
    best_week: Optional[datetime]
    longest_streak: int
    completion_rate: float


# Pagination Schemas
class PaginationParams(BaseSchema):
    """Pagination parameters schema."""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class PaginatedResponse(BaseSchema):
    """Paginated response schema."""
    items: List[Any]
    page: int
    page_size: int
    total: int
    pages: int


# Error Schemas
class ErrorDetail(BaseSchema):
    """Error detail schema."""
    type: str
    title: str
    status: int
    detail: str
    fields: Optional[Dict[str, List[str]]] = None


# Filter Schemas
class GoalFilters(BaseSchema):
    """Goal filters schema."""
    status: Optional[str] = Field(None, pattern="^(draft|active|ended)$")
    goal_type: Optional[str] = Field(None, pattern="^(count|sum|streak|milestone|open)$")
    privacy: Optional[str] = Field(None, pattern="^(public|unlisted|private)$")
    q: Optional[str] = Field(None, min_length=1, max_length=100)


class LogFilters(BaseSchema):
    """Log filters schema."""
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    order: str = Field("desc", pattern="^(asc|desc)$")


# Health Check Schema
class HealthCheck(BaseSchema):
    """Health check schema."""
    status: str
    version: str
    database: str
    timestamp: datetime
