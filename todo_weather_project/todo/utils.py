from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import Notification
from datetime import datetime, timedelta
from celery import shared_task
import logging

logger = logging.getLogger(__name__)

def create_notification(user, type, title, message, task=None):
    """Create a notification for a user"""
    try:
        notification = Notification.objects.create(
            user=user,
            type=type,
            title=title,
            message=message,
            task=task
        )
        
        # Send email notification if user has email notifications enabled
        if user.profile.email_notifications:
            send_notification_email(notification)
        
        return notification
    except Exception as e:
        logger.error(f"Error creating notification: {e}")
        return None

def send_notification_email(notification):
    """Send email for notification"""
    subject = f'Todo App: {notification.title}'
    html_message = render_to_string('todo/emails/notification.html', {
        'notification': notification,
        'user': notification.user,
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [notification.user.email],
        html_message=html_message,
        fail_silently=True,
    )

def parse_tags(tags_string):
    """Parse comma-separated tags string into list"""
    if not tags_string:
        return []
    return [tag.strip() for tag in tags_string.split(',') if tag.strip()]

def format_duration(minutes):
    """Format minutes into readable duration"""
    if minutes < 60:
        return f"{minutes} minutes"
    elif minutes < 1440:
        hours = minutes // 60
        return f"{hours} hour{'s' if hours > 1 else ''}"
    else:
        days = minutes // 1440
        return f"{days} day{'s' if days > 1 else ''}"

def get_task_statistics(user, days=30):
    """Get task statistics for user over specified days"""
    from django.db.models import Count, Q
    from .models import TodoItem
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    tasks = TodoItem.objects.filter(
        user=user,
        created_date__range=[start_date, end_date]
    )
    
    stats = {
        'total': tasks.count(),
        'completed': tasks.filter(completed=True).count(),
        'by_priority': tasks.values('priority').annotate(count=Count('id')),
        'by_category': tasks.values('category').annotate(count=Count('id')),
        'overdue': tasks.filter(
            completed=False,
            due_date__lt=end_date
        ).count(),
    }
    
    return stats

# Celery tasks
@shared_task
def check_task_reminders():
    """Check for tasks that need reminders"""
    from .models import TodoItem
    from datetime import timedelta
    from django.utils import timezone
    
    now = timezone.now()
    reminder_threshold = now + timedelta(hours=24)
    
    # Tasks due within 24 hours that haven't had reminder sent
    tasks_to_remind = TodoItem.objects.filter(
        completed=False,
        due_date__lte=reminder_threshold,
        due_date__gte=now,
        reminder_sent=False
    ).select_related('user')
    
    for task in tasks_to_remind:
        try:
            # Send reminder email
            from .views import send_task_reminder_email
            send_task_reminder_email(task)
            
            # Create notification
            create_notification(
                user=task.user,
                type='reminder',
                title=f'Task Due Soon: {task.title}',
                message=f'Your task "{task.title}" is due on {task.due_date.strftime("%Y-%m-%d %H:%M")}',
                task=task
            )
            
            # Mark reminder as sent
            task.reminder_sent = True
            task.save()
            
        except Exception as e:
            logger.error(f"Error sending reminder for task {task.id}: {e}")

@shared_task
def send_daily_summaries():
    """Send daily summaries to users who opted in"""
    from django.contrib.auth.models import User
    
    users = User.objects.filter(
        profile__daily_summary=True,
        profile__email_notifications=True
    )
    
    for user in users:
        try:
            from .views import send_daily_summary
            send_daily_summary(user)
        except Exception as e:
            logger.error(f"Error sending daily summary to {user.email}: {e}")

@shared_task
def cleanup_old_notifications():
    """Delete notifications older than 30 days"""
    from .models import Notification
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=30)
    old_notifications = Notification.objects.filter(created_at__lt=cutoff_date)
    count = old_notifications.count()
    old_notifications.delete()
    
    logger.info(f"Deleted {count} old notifications")