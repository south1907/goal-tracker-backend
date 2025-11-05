"""
SQLAlchemy models for the Goal Tracker application.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    TypeDecorator,
    func,
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class LowercaseStringEnum(TypeDecorator):
    """Type decorator that converts enum strings to lowercase."""
    impl = String(20)
    cache_ok = True
    
    def __init__(self, enum_class):
        super().__init__()
        self.enum_class = enum_class
    
    def process_bind_param(self, value, dialect):
        """Convert enum to lowercase string when writing to database."""
        if value is None:
            return None
        if isinstance(value, self.enum_class):
            return value.value
        if isinstance(value, str):
            return value.lower()
        return str(value).lower()
    
    def process_result_value(self, value, dialect):
        """Convert string from database to enum, handling uppercase."""
        if value is None:
            return None
        if isinstance(value, str):
            # Convert to lowercase first
            value_lower = value.lower()
            # Try to get enum by value
            try:
                return self.enum_class(value_lower)
            except ValueError:
                # If not found by value, try to find by name (uppercase to enum)
                for enum_member in self.enum_class:
                    if enum_member.name == value.upper():
                        return enum_member
                # Fallback: return the lowercase string (will be converted by Pydantic)
                return value_lower
        return value


class GoalType(str, Enum):
    """Goal type enumeration."""
    COUNT = "count"
    SUM = "sum"
    STREAK = "streak"
    MILESTONE = "milestone"
    OPEN = "open"


class TimeframeType(str, Enum):
    """Timeframe type enumeration."""
    FIXED = "fixed"
    ROLLING = "rolling"
    RECURRING = "recurring"


class PrivacyLevel(str, Enum):
    """Privacy level enumeration."""
    PUBLIC = "public"
    UNLISTED = "unlisted"
    PRIVATE = "private"


class GoalStatus(str, Enum):
    """Goal status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    ENDED = "ended"


class MemberRole(str, Enum):
    """Goal member role enumeration."""
    OWNER = "owner"
    EDITOR = "editor"
    MEMBER = "member"
    VIEWER = "viewer"


class User(Base):
    """User model."""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    goals: Mapped[List["Goal"]] = relationship("Goal", back_populates="owner")
    logs: Mapped[List["Log"]] = relationship("Log", back_populates="user")
    goal_memberships: Mapped[List["GoalMember"]] = relationship("GoalMember", back_populates="user")


class Goal(Base):
    """Goal model."""
    
    __tablename__ = "goals"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    emoji: Mapped[str] = mapped_column(String(10), nullable=False)
    goal_type: Mapped[GoalType] = mapped_column(
        LowercaseStringEnum(GoalType),  # Automatically converts uppercase to lowercase
        nullable=False
    )
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    target: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    
    # Timeframe
    timeframe_type: Mapped[TimeframeType] = mapped_column(
        LowercaseStringEnum(TimeframeType),  # Automatically converts uppercase to lowercase
        nullable=False
    )
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    rolling_days: Mapped[Optional[int]] = mapped_column(Integer)
    rrule: Mapped[Optional[str]] = mapped_column(Text)  # Recurrence rule
    
    # Settings
    privacy: Mapped[PrivacyLevel] = mapped_column(
        LowercaseStringEnum(PrivacyLevel),  # Automatically converts uppercase to lowercase
        nullable=False
    )
    status: Mapped[GoalStatus] = mapped_column(
        LowercaseStringEnum(GoalStatus),  # Automatically converts uppercase to lowercase
        nullable=False
    )
    settings_json: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # Sharing
    share_token: Mapped[Optional[str]] = mapped_column(String(36), unique=True, index=True, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="goals")
    logs: Mapped[List["Log"]] = relationship("Log", back_populates="goal")
    members: Mapped[List["GoalMember"]] = relationship("GoalMember", back_populates="goal")
    cycle_summaries: Mapped[List["CycleSummary"]] = relationship("CycleSummary", back_populates="goal")
    
    # Indexes
    __table_args__ = (
        Index("idx_goal_owner_status", "owner_id", "status"),
        Index("idx_goal_status_timeframe", "status", "timeframe_type"),
        Index("idx_goal_fulltext", "name", "description", mysql_prefix="FULLTEXT"),
    )


class GoalMember(Base):
    """Goal member model for team goals."""
    
    __tablename__ = "goal_members"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    goal_id: Mapped[int] = mapped_column(ForeignKey("goals.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    role: Mapped[MemberRole] = mapped_column(
        LowercaseStringEnum(MemberRole),  # Automatically converts uppercase to lowercase
        nullable=False
    )
    
    # Relationships
    goal: Mapped["Goal"] = relationship("Goal", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="goal_memberships")
    
    # Indexes
    __table_args__ = (
        Index("idx_goal_member_unique", "goal_id", "user_id", unique=True),
    )


class Log(Base):
    """Log entry model."""
    
    __tablename__ = "logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    goal_id: Mapped[int] = mapped_column(ForeignKey("goals.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    note: Mapped[Optional[str]] = mapped_column(Text)
    attachment_url: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    goal: Mapped["Goal"] = relationship("Goal", back_populates="logs")
    user: Mapped["User"] = relationship("User", back_populates="logs")
    
    # Indexes
    __table_args__ = (
        Index("idx_log_goal_date", "goal_id", "date"),
        Index("idx_log_user_goal", "user_id", "goal_id"),
    )


class CycleSummary(Base):
    """Cycle summary model for computed statistics."""
    
    __tablename__ = "cycle_summaries"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    goal_id: Mapped[int] = mapped_column(ForeignKey("goals.id"), nullable=False)
    cycle_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    achieved: Mapped[bool] = mapped_column(Boolean, nullable=False)
    streak_max: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    goal: Mapped["Goal"] = relationship("Goal", back_populates="cycle_summaries")
    
    # Indexes
    __table_args__ = (
        Index("idx_cycle_goal_index", "goal_id", "cycle_index"),
    )


class ApiKey(Base):
    """API key model for external integrations."""
    
    __tablename__ = "api_keys"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    user: Mapped["User"] = relationship("User")
