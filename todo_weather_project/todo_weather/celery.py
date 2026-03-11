import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'todo_weather.settings')

app = Celery('todo_weather')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps
app.autodiscover_tasks()

# Configure periodic tasks
app.conf.beat_schedule = {
    'check-task-reminders': {
        'task': 'todo.utils.check_task_reminders',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
    'send-daily-summaries': {
        'task': 'todo.utils.send_daily_summaries',
        'schedule': crontab(hour=8, minute=0),  # 8 AM daily
    },
    'cleanup-old-notifications': {
        'task': 'todo.utils.cleanup_old_notifications',
        'schedule': crontab(hour=0, minute=0),  # Midnight daily
    },
}