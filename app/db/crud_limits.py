"""
CRUD operations for limits management
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.limits_db import (
    UserLimit, LimitTemplate, LimitViolation, 
    LimitNotification, LimitTypes, LimitActions,
    BASIC_TEMPLATE, PREMIUM_TEMPLATE, ENTERPRISE_TEMPLATE
)
from app.models.user import User


def create_user_limit(
    db: Session, 
    username: str, 
    limit_type: str, 
    limit_value: int,
    action: str = "notify",
    **kwargs
) -> UserLimit:
    """Create a new user limit"""
    user_limit = UserLimit(
        username=username,
        limit_type=limit_type,
        limit_value=limit_value,
        action=action,
        created_at=datetime.utcnow(),
        **kwargs
    )
    db.add(user_limit)
    db.commit()
    db.refresh(user_limit)
    return user_limit


def get_user_limits(db: Session, username: str) -> List[UserLimit]:
    """Get all limits for a user"""
    return db.query(UserLimit).filter(UserLimit.username == username).all()


def get_user_limit(db: Session, username: str, limit_type: str) -> Optional[UserLimit]:
    """Get specific limit for a user"""
    return db.query(UserLimit).filter(
        UserLimit.username == username,
        UserLimit.limit_type == limit_type,
        UserLimit.enabled == True
    ).first()


def update_user_limit(
    db: Session, 
    username: str, 
    limit_type: str, 
    **kwargs
) -> Optional[UserLimit]:
    """Update user limit"""
    user_limit = get_user_limit(db, username, limit_type)
    if user_limit:
        for key, value in kwargs.items():
            setattr(user_limit, key, value)
        user_limit.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user_limit)
    return user_limit


def delete_user_limit(db: Session, username: str, limit_type: str) -> bool:
    """Delete user limit"""
    user_limit = get_user_limit(db, username, limit_type)
    if user_limit:
        db.delete(user_limit)
        db.commit()
        return True
    return False


def create_limit_violation(
    db: Session,
    username: str,
    limit_type: str,
    current_value: int,
    limit_value: int,
    action_taken: str,
    **kwargs
) -> LimitViolation:
    """Record a limit violation"""
    violation = LimitViolation(
        username=username,
        limit_type=limit_type,
        current_value=current_value,
        limit_value=limit_value,
        action_taken=action_taken,
        violation_time=datetime.utcnow(),
        **kwargs
    )
    db.add(violation)
    db.commit()
    db.refresh(violation)
    return violation


def get_user_violations(
    db: Session, 
    username: str, 
    limit: Optional[int] = None
) -> List[LimitViolation]:
    """Get violations for a user"""
    query = db.query(LimitViolation).filter(LimitViolation.username == username)
    if limit:
        query = query.limit(limit)
    return query.order_by(LimitViolation.violation_time.desc()).all()


def get_active_violations_count(db: Session) -> int:
    """Get count of active (unresolved) violations"""
    return db.query(LimitViolation).filter(LimitViolation.resolved == False).count()


def resolve_violation(db: Session, violation_id: int) -> bool:
    """Mark a violation as resolved"""
    violation = db.query(LimitViolation).filter(LimitViolation.id == violation_id).first()
    if violation:
        violation.resolved = True
        violation.resolved_at = datetime.utcnow()
        db.commit()
        return True
    return False


def create_limit_template(
    db: Session,
    name: str,
    description: str,
    is_default: bool = False,
    created_by: str,
    **kwargs
) -> LimitTemplate:
    """Create a new limit template"""
    template = LimitTemplate(
        name=name,
        description=description,
        is_default=is_default,
        created_by=created_by,
        created_at=datetime.utcnow(),
        **kwargs
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def get_limit_templates(db: Session, active_only: bool = True) -> List[LimitTemplate]:
    """Get all limit templates"""
    query = db.query(LimitTemplate)
    if active_only:
        query = query.filter(LimitTemplate.is_active == True)
    return query.order_by(LimitTemplate.name).all()


def apply_template_to_user(
    db: Session,
    username: str,
    template_id: int
) -> bool:
    """Apply a template to a user"""
    template = db.query(LimitTemplate).filter(LimitTemplate.id == template_id).first()
    if not template:
        return False
    
    # Delete existing limits for this user
    existing_limits = get_user_limits(db, username)
    for limit in existing_limits:
        delete_user_limit(db, username, limit.limit_type)
    
    # Apply template rules
    for rule in template.rules:
        create_user_limit(db, username, rule['limit_type'], rule['value'], rule['action'])
    
    return True


def get_users_with_limits_count(db: Session) -> int:
    """Get count of users with any limits"""
    from sqlalchemy import func
    return db.query(UserLimit.username).distinct().count()


def check_user_limits(db: Session, username: str, current_usage: Dict[str, int]) -> Dict[str, Any]:
    """Check if user exceeds any limits and return actions to take"""
    user_limits = get_user_limits(db, username)
    results = {}
    
    for limit in user_limits:
        if not limit.enabled:
            continue
            
        limit_type = limit.limit_type
        limit_value = limit.limit_value
        current_value = current_usage.get(limit_type, 0)
        
        if current_value >= limit_value:
            # Calculate percentage
        percentage = (current_value / limit_value) * 100 if limit_value > 0 else 0
            
            results[limit_type] = {
                'exceeded': True,
                'percentage': percentage,
                'action': limit.action,
                'threshold': limit.notification_threshold,
                'should_notify': percentage >= (limit.notification_threshold * 100)
            }
        else:
            results[limit_type] = {
                'exceeded': False,
                'percentage': percentage,
                'action': None,
                'threshold': limit.notification_threshold,
                'should_notify': False
            }
    
    return results


def get_limits_stats(db: Session) -> Dict[str, int]:
    """Get comprehensive statistics about limits"""
    from sqlalchemy import func
    
    return {
        'total_users_with_limits': get_users_with_limits_count(db),
        'active_violations': get_active_violations_count(db),
        'total_templates': db.query(LimitTemplate).count(),
        'active_templates': db.query(LimitTemplate).filter(LimitTemplate.is_active == True).count(),
        'total_violations': db.query(LimitViolation).count(),
        'notifications_enabled': db.query(LimitNotification).filter(LimitNotification.enabled == True).count()
    }


def initialize_default_templates(db: Session, admin_username: str):
    """Initialize default templates if they don't exist"""
    existing_templates = {t.name: t for t in get_limit_templates(db, active_only=False)}
    
    default_templates = [BASIC_TEMPLATE, PREMIUM_TEMPLATE, ENTERPRISE_TEMPLATE]
    
    for template in default_templates:
        if template['name'] not in existing_templates:
            create_limit_template(
                db=db,
                name=template['name'],
                description=template['description'],
                is_default=template['is_default'],
                created_by=admin_username
            )
