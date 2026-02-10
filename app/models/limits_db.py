"""
SQLAlchemy models for limits database tables
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, BigInteger, Boolean, Text, DateTime, Float, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class UserLimit(Base):
    """User limits configuration"""
    __tablename__ = 'user_limits'
    
    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String(32), nullable=False, index=True)
    limit_type = Column(String(50), nullable=False, index=True)
    limit_value = Column(BigInteger, nullable=False)
    action = Column(String(20), nullable=True, default='notify')  # notify, disable, throttle, delete
    enabled = Column(Boolean, nullable=True, default=True)
    notification_threshold = Column(Float, nullable=True, default=0.8)  # 80% by default
    webhook_url = Column(String(500), nullable=True)
    webhook_enabled = Column(Boolean, nullable=True, default=False)
    auto_reset_enabled = Column(Boolean, nullable=True, default=True)
    reset_schedule = Column(String(100), nullable=True)  # cron expression
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)
    
    # Unique constraint on username + limit_type
    __table_args__ = (
        Index('idx_user_limits_username', 'username'),
        Index('idx_user_limits_type', 'limit_type'),
        {'sqlite_autoincrement': True}
    )


class LimitTemplate(Base):
    """Reusable limit templates"""
    __tablename__ = 'limit_templates'
    
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_default = Column(Boolean, nullable=True, default=False)
    is_active = Column(Boolean, nullable=True, default=True)
    created_by = Column(String(32), nullable=True)  # admin username
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_limit_templates_name', 'name'),
        {'sqlite_autoincrement': True}
    )


class LimitViolation(Base):
    """History of limit violations"""
    __tablename__ = 'limit_violations'
    
    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String(32), nullable=False, index=True)
    limit_type = Column(String(50), nullable=False, index=True)
    current_value = Column(BigInteger, nullable=False)
    limit_value = Column(BigInteger, nullable=False)
    violation_time = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    action_taken = Column(String(20), nullable=False)  # notify, disable, throttle, delete
    resolved = Column(Boolean, nullable=True, default=False)
    resolved_at = Column(DateTime, nullable=True)
    notification_sent = Column(Boolean, nullable=True, default=False)
    admin_notes = Column(Text, nullable=True)
    
    __table_args__ = (
        Index('idx_limit_violations_username', 'username'),
        Index('idx_limit_violations_time', 'violation_time'),
        {'sqlite_autoincrement': True}
    )


class LimitNotification(Base):
    """Notification settings for limits"""
    __tablename__ = 'limit_notifications'
    
    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String(32), nullable=False, index=True)
    limit_type = Column(String(50), nullable=False, index=True)
    notification_type = Column(String(20), nullable=False)  # email, telegram, webhook
    enabled = Column(Boolean, nullable=True, default=True)
    threshold_percentage = Column(Float, nullable=True, default=0.8)  # 80% by default
    recipient = Column(String(500), nullable=True)  # email, chat_id, webhook_url
    template_id = Column(Integer, ForeignKey('limit_templates.id'), nullable=True)
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    
    # Relationship with template
    template = relationship("LimitTemplate", backref="notifications")
    
    __table_args__ = (
        Index('idx_limit_notifications_username', 'username'),
        {'sqlite_autoincrement': True}
    )


# Predefined limit types
class LimitTypes:
    DATA_LIMIT = "data_limit"
    TIME_LIMIT = "time_limit"
    CONNECTION_LIMIT = "connection_limit"
    SPEED_LIMIT = "speed_limit"
    DAILY_LIMIT = "daily_limit"
    WEEKLY_LIMIT = "weekly_limit"
    MONTHLY_LIMIT = "monthly_limit"


# Predefined actions
class LimitActions:
    NOTIFY = "notify"
    DISABLE = "disable"
    THROTTLE = "throttle"
    DELETE = "delete"


# Predefined templates as Python objects
BASIC_TEMPLATE = {
    "name": "Basic Plan",
    "description": "Basic user with standard limits",
    "rules": [
        {"limit_type": LimitTypes.DATA_LIMIT, "value": 10737418240, "action": LimitActions.NOTIFY},  # 10GB
        {"limit_type": LimitTypes.TIME_LIMIT, "value": 2592000, "action": LimitActions.NOTIFY},  # 30 days
    ],
    "is_default": True
}

PREMIUM_TEMPLATE = {
    "name": "Premium Plan",
    "description": "Premium user with higher limits",
    "rules": [
        {"limit_type": LimitTypes.DATA_LIMIT, "value": 107374182400, "action": LimitActions.NOTIFY},  # 100GB
        {"limit_type": LimitTypes.TIME_LIMIT, "value": 7776000, "action": LimitActions.NOTIFY},  # 90 days
        {"limit_type": LimitTypes.CONNECTION_LIMIT, "value": 5, "action": LimitActions.NOTIFY},
    ],
    "is_default": False
}

ENTERPRISE_TEMPLATE = {
    "name": "Enterprise Plan",
    "description": "Enterprise user with maximum limits",
    "rules": [
        {"limit_type": LimitTypes.DATA_LIMIT, "value": 1073741824000, "action": LimitActions.NOTIFY},  # 1TB
        {"limit_type": LimitTypes.TIME_LIMIT, "value": 31536000, "action": LimitActions.NOTIFY},  # 365 days
        {"limit_type": LimitTypes.CONNECTION_LIMIT, "value": 20, "action": LimitActions.NOTIFY},
        {"limit_type": LimitTypes.SPEED_LIMIT, "value": 104857600, "action": LimitActions.THROTTLE},  # 100MB/s
    ],
    "is_default": False
}
