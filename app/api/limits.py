"""
API endpoints for advanced limits management
"""

from datetime import datetime
from typing import List, Dict, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.limits_db import (
    UserLimit, LimitTemplate, LimitViolation, 
    LimitNotification, LimitTypes, LimitActions,
    BASIC_TEMPLATE, PREMIUM_TEMPLATE, ENTERPRISE_TEMPLATE
)
from app.db.crud_limits import (
    create_user_limit, get_user_limits, get_user_limit,
    update_user_limit, delete_user_limit,
    create_limit_violation, get_user_violations,
    resolve_violation, get_active_violations_count,
    create_limit_template, get_limit_templates,
    apply_template_to_user, get_users_with_limits_count,
    check_user_limits, get_limits_stats,
    initialize_default_templates
)
from app.models.user import User, get_db_user
from app.dependencies import get_admin
from app.models.admin import Admin

router = APIRouter(prefix="/api/limits", tags=["limits"])


@router.get("/templates", response_model=List[LimitTemplate])
async def get_limit_templates(
    admin: Admin = Depends(get_admin),
    db: Session = Depends(get_db)
):
    """Get all available limit templates"""
    return get_limit_templates(db, active_only=True)


@router.post("/templates", response_model=LimitTemplate)
async def create_limit_template(
    template: LimitTemplate,
    admin: Admin = Depends(get_admin),
    db: Session = Depends(get_db)
):
    """Create a new limit template"""
    return create_limit_template(db, template.name, template.description, admin.username)


@router.get("/users/{username}", response_model=List[UserLimit])
async def get_user_limits(
    username: str,
    admin: Admin = Depends(get_admin),
    db: Session = Depends(get_db)
):
    """Get current limits status for a user"""
    user = get_db_user(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return get_user_limits(db, username)


@router.post("/users/{username}", response_model=Dict[str, str])
async def set_user_limits(
    username: str,
    limits: Dict[str, Any],
    admin: Admin = Depends(get_admin),
    db: Session = Depends(get_db)
):
    """Set advanced limits for a user"""
    user = get_db_user(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    results = {}
    for limit_type, limit_data in limits.items():
        limit_rule = create_user_limit(
            db=db,
            username=username,
            limit_type=limit_type,
            limit_value=limit_data.get('value', 0),
            action=limit_data.get('action', 'notify'),
            notification_threshold=limit_data.get('notification_threshold', 0.8),
            webhook_url=limit_data.get('webhook_url'),
            webhook_enabled=limit_data.get('webhook_enabled', False),
            auto_reset_enabled=limit_data.get('auto_reset_enabled', True),
            reset_schedule=limit_data.get('reset_schedule'),
            description=limit_data.get('description')
        )
        results[limit_type] = f"Limit {limit_type} set successfully"
    
    return results


@router.get("/users/{username}/violations", response_model=List[LimitViolation])
async def get_user_violations(
    username: str,
    limit: Optional[int] = Query(None, description="Maximum number of violations to return"),
    admin: Admin = Depends(get_admin),
    db: Session = Depends(get_db)
):
    """Get limit violations for a user"""
    user = get_db_user(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return get_user_violations(db, username, limit)


@router.post("/users/{username}/check")
async def check_user_limits(
    username: str,
    current_usage: Dict[str, int],
    admin: Admin = Depends(get_admin),
    db: Session = Depends(get_db)
):
    """Manually check and enforce user limits"""
    user = get_db_user(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check all limits and take actions
    results = check_user_limits(db, username, current_usage)
    return results


@router.post("/users/{username}/apply-template")
async def apply_template_to_user(
    username: str,
    template_id: int,
    admin: Admin = Depends(get_admin),
    db: Session = Depends(get_db)
):
    """Apply a template to a user"""
    user = get_db_user(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    success = apply_template_to_user(db, username, template_id)
    if success:
        return {"message": f"Template {template_id} applied successfully to {username}"}
    else:
        raise HTTPException(status_code=400, detail="Failed to apply template")


@router.get("/stats", response_model=Dict[str, int])
async def get_limits_stats(
    admin: Admin = Depends(get_admin),
    db: Session = Depends(get_db)
):
    """Get statistics about limits usage"""
    return get_limits_stats(db)


@router.post("/initialize")
async def initialize_templates(
    admin: Admin = Depends(get_admin),
    db: Session = Depends(get_db)
):
    """Initialize default templates"""
    initialize_default_templates(db, admin.username)
    return {"message": "Default templates initialized"}


@router.delete("/users/{username}/{limit_type}")
async def delete_user_limit(
    username: str,
    limit_type: str,
    admin: Admin = Depends(get_admin),
    db: Session = Depends(get_db)
):
    """Delete a specific limit for a user"""
    user = get_db_user(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    success = delete_user_limit(db, username, limit_type)
    if success:
        return {"message": f"Limit {limit_type} deleted for {username}"}
    else:
        raise HTTPException(status_code=400, detail="Failed to delete limit")
