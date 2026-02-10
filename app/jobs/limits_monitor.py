"""
Background job for monitoring user limits
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

from app import logger, xray
from app.db import Session, crud, get_db
from app.db.crud_limits import (
    check_user_limits, create_limit_violation,
    get_user_limits, get_users_with_limits_count
)
from app.models.limits_db import LimitTypes, LimitActions
from app.models.user import User
from app.utils import report


class LimitsMonitor:
    """Background service for monitoring user limits"""
    
    def __init__(self):
        self.check_interval = 300  # 5 minutes
        self.notification_threshold = 0.8  # 80%
        self.running = False
    
    async def start(self):
        """Start the limits monitor"""
        if self.running:
            return
        
        self.running = True
        logger.info("Limits monitor started")
        
        while self.running:
            try:
                await self.check_all_users()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in limits monitor: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def stop(self):
        """Stop the limits monitor"""
        self.running = False
        logger.info("Limits monitor stopped")
    
    async def check_all_users(self):
        """Check limits for all users"""
        with Session() as db:
            # Get all users with limits
            users_with_limits = crud.get_users_with_limits(db)
            
            for user in users_with_limits:
                try:
                    await self.check_user_limits(db, user)
                except Exception as e:
                    logger.error(f"Error checking limits for user {user.username}: {e}")
    
    async def check_user_limits(self, db: Session, user: User):
        """Check limits for a single user"""
        # Get current usage from xray
        current_usage = await self.get_current_usage(user.username)
        
        # Check against database limits
        limit_checks = check_user_limits(db, user.username, current_usage)
        
        for limit_type, check_result in limit_checks.items():
            if check_result['exceeded']:
                await self.handle_limit_exceeded(
                    db, user, limit_type, 
                    current_usage.get(limit_type, 0),
                    check_result
                )
            elif check_result['should_notify']:
                await self.send_warning_notification(
                    db, user, limit_type, check_result
                )
    
    async def get_current_usage(self, username: str) -> Dict[str, int]:
        """Get current usage for a user from xray stats"""
        try:
            # Get user stats from xray
            user_stats = xray.api.get_user_stats(username)
            
            if not user_stats:
                return {}
            
            usage = {
                'data_limit': user_stats.get('uptime', 0),  # bytes transferred
                'time_limit': user_stats.get('uptime', 0),  # seconds online
                'connection_limit': len(user_stats.get('connections', [])),  # active connections
            }
            
            # Calculate daily/weekly/monthly usage
            usage.update(await self.calculate_periodic_usage(username))
            
            return usage
            
        except Exception as e:
            logger.error(f"Error getting usage for {username}: {e}")
            return {}
    
    async def calculate_periodic_usage(self, username: str) -> Dict[str, int]:
        """Calculate daily/weekly/monthly usage"""
        # This would require historical data storage
        # For now, return basic calculations
        return {
            'daily_limit': 0,  # Would need daily tracking
            'weekly_limit': 0,  # Would need weekly tracking
            'monthly_limit': 0,  # Would need monthly tracking
        }
    
    async def handle_limit_exceeded(
        self, 
        db: Session, 
        user: User, 
        limit_type: str,
        current_value: int,
        check_result: Dict[str, Any]
    ):
        """Handle when a limit is exceeded"""
        action = check_result['action']
        
        # Record violation
        violation = create_limit_violation(
            db=db,
            username=user.username,
            limit_type=limit_type,
            current_value=current_value,
            limit_value=check_result.get('limit_value', 0),
            action_taken=action
        )
        
        # Take action based on limit type
        if action == LimitActions.DISABLE:
            await self.disable_user(user)
        elif action == LimitActions.THROTTLE:
            await self.throttle_user(user, limit_type)
        elif action == LimitActions.DELETE:
            await self.delete_user(user)
        
        # Send notification
        await self.send_violation_notification(db, user, limit_type, violation)
        
        # Log the action
        logger.warning(
            f"User {user.username} exceeded {limit_type} limit. "
            f"Action: {action}, Current: {current_value}"
        )
        
        # Report to admin
        report.user_limit_exceeded(
            user=user,
            limit_type=limit_type,
            current_value=current_value,
            limit_value=check_result.get('limit_value', 0),
            action_taken=action
        )
    
    async def disable_user(self, user: User):
        """Disable a user"""
        try:
            crud.update_user(db, user.username, {"status": "disabled"})
            xray.operations.remove_user(user.username)
            logger.info(f"User {user.username} disabled due to limit exceeded")
        except Exception as e:
            logger.error(f"Error disabling user {user.username}: {e}")
    
    async def throttle_user(self, user: User, limit_type: str):
        """Throttle user connection"""
        try:
            # This would require xray configuration changes
            # For now, just log the action
            logger.info(f"User {user.username} throttled for {limit_type}")
        except Exception as e:
            logger.error(f"Error throttling user {user.username}: {e}")
    
    async def delete_user(self, user: User):
        """Delete a user"""
        try:
            crud.remove_user(db, user.username)
            xray.operations.remove_user(user.username)
            logger.info(f"User {user.username} deleted due to limit exceeded")
        except Exception as e:
            logger.error(f"Error deleting user {user.username}: {e}")
    
    async def send_warning_notification(
        self, 
        db: Session, 
        user: User, 
        limit_type: str,
        check_result: Dict[str, Any]
    ):
        """Send warning notification when approaching limit"""
        percentage = check_result['percentage']
        threshold = check_result['threshold'] * 100
        
        # Get notification settings for this user/limit
        notifications = crud.get_limit_notifications(db, user.username, limit_type)
        
        for notification in notifications:
            if notification.enabled and percentage >= threshold:
                await self.send_notification(
                    notification.notification_type,
                    notification.recipient,
                    f"User {user.username} has used {percentage:.1f}% of {limit_type} limit"
                )
    
    async def send_violation_notification(
        self, 
        db: Session, 
        user: User, 
        limit_type: str,
        violation
    ):
        """Send notification when limit is violated"""
        notifications = crud.get_limit_notifications(db, user.username, limit_type)
        
        for notification in notifications:
            if notification.enabled:
                await self.send_notification(
                    notification.notification_type,
                    notification.recipient,
                    f"User {user.username} exceeded {limit_type} limit. "
                    f"Action taken: {violation.action_taken}"
                )
    
    async def send_notification(self, notification_type: str, recipient: str, message: str):
        """Send notification via specified channel"""
        try:
            if notification_type == "email":
                await self.send_email(recipient, message)
            elif notification_type == "telegram":
                await self.send_telegram(recipient, message)
            elif notification_type == "webhook":
                await self.send_webhook(recipient, message)
        except Exception as e:
            logger.error(f"Error sending {notification_type} notification: {e}")
    
    async def send_email(self, email: str, message: str):
        """Send email notification"""
        # Implementation would depend on email service
        logger.info(f"Email notification to {email}: {message}")
    
    async def send_telegram(self, chat_id: str, message: str):
        """Send Telegram notification"""
        # Implementation would depend on telegram bot
        logger.info(f"Telegram notification to {chat_id}: {message}")
    
    async def send_webhook(self, webhook_url: str, message: str):
        """Send webhook notification"""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "marzban-limits"
                }
                
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Webhook sent successfully to {webhook_url}")
                    else:
                        logger.error(f"Webhook failed with status {response.status}")
        except Exception as e:
            logger.error(f"Error sending webhook: {e}")


# Global instance
limits_monitor = LimitsMonitor()


def start_limits_monitor():
    """Start the limits monitor background task"""
    from app import scheduler
    
    scheduler.add_job(
        limits_monitor.start,
        "interval",
        seconds=10,  # Start after 10 seconds
        id="limits_monitor"
    )
    
    logger.info("Limits monitor scheduled")


def stop_limits_monitor():
    """Stop the limits monitor background task"""
    from app import scheduler
    
    scheduler.remove_job("limits_monitor")
    asyncio.create_task(limits_monitor.stop())
    
    logger.info("Limits monitor stopped")
