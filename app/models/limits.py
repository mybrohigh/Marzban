"""
Advanced User Limits System for Marzban
Enhanced limits management with custom rules and notifications
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict


class LimitType(str, Enum):
    """Types of limits that can be applied to users"""
    data_limit = "data_limit"
    time_limit = "time_limit"
    connection_limit = "connection_limit"
    speed_limit = "speed_limit"
    daily_limit = "daily_limit"
    weekly_limit = "weekly_limit"
    monthly_limit = "monthly_limit"


class LimitAction(str, Enum):
    """Actions to take when limit is reached"""
    disable = "disable"
    notify = "notify"
    throttle = "throttle"
    delete = "delete"


class LimitRule(BaseModel):
    """Individual limit rule"""
    limit_type: LimitType
    value: int
    action: LimitAction = LimitAction.notify
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    description: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class AdvancedUserLimits(BaseModel):
    """Advanced limits configuration for a user"""
    username: str
    rules: List[LimitRule] = []
    auto_reset_enabled: bool = True
    reset_schedule: Optional[str] = None  # cron expression
    notification_threshold: float = 0.8  # 80% by default
    webhook_url: Optional[str] = None
    webhook_enabled: bool = False
    
    model_config = ConfigDict(from_attributes=True)


class LimitTemplate(BaseModel):
    """Reusable limit templates"""
    name: str
    description: str
    rules: List[LimitRule]
    is_default: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    
    model_config = ConfigDict(from_attributes=True)


class LimitViolation(BaseModel):
    """Record of limit violations"""
    username: str
    limit_type: LimitType
    violation_time: datetime = Field(default_factory=datetime.now)
    current_value: int
    limit_value: int
    action_taken: LimitAction
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class LimitNotification(BaseModel):
    """Notification configuration for limits"""
    enabled: bool = True
    email_enabled: bool = False
    telegram_enabled: bool = False
    webhook_enabled: bool = False
    email_addresses: List[str] = []
    telegram_chat_ids: List[str] = []
    webhook_urls: List[str] = []
    notification_threshold: float = 0.8
    
    model_config = ConfigDict(from_attributes=True)


class UserLimitStatus(BaseModel):
    """Current limit status for a user"""
    username: str
    limits: Dict[LimitType, LimitRule]
    current_usage: Dict[LimitType, int]
    percentage_used: Dict[LimitType, float]
    is_limited: bool = False
    violations_count: int = 0
    last_violation: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# Predefined limit templates
DEFAULT_TEMPLATES = [
    LimitTemplate(
        name="Basic Plan",
        description="Basic user with standard limits",
        rules=[
            LimitRule(limit_type=LimitType.data_limit, value=10737418240, action=LimitAction.notify),  # 10GB
            LimitRule(limit_type=LimitType.time_limit, value=2592000, action=LimitAction.notify),  # 30 days
        ],
        is_default=True
    ),
    LimitTemplate(
        name="Premium Plan",
        description="Premium user with higher limits",
        rules=[
            LimitRule(limit_type=LimitType.data_limit, value=107374182400, action=LimitAction.notify),  # 100GB
            LimitRule(limit_type=LimitType.time_limit, value=7776000, action=LimitAction.notify),  # 90 days
            LimitRule(limit_type=LimitType.connection_limit, value=5, action=LimitAction.notify),
        ],
        is_default=False
    ),
    LimitTemplate(
        name="Enterprise Plan",
        description="Enterprise user with maximum limits",
        rules=[
            LimitRule(limit_type=LimitType.data_limit, value=1073741824000, action=LimitAction.notify),  # 1TB
            LimitRule(limit_type=LimitType.time_limit, value=31536000, action=LimitAction.notify),  # 365 days
            LimitRule(limit_type=LimitType.connection_limit, value=20, action=LimitAction.notify),
            LimitRule(limit_type=LimitType.speed_limit, value=104857600, action=LimitAction.throttle),  # 100MB/s
        ],
        is_default=False
    ),
]
