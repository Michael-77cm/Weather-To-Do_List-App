import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weather_todo_project.settings')

app = Celery('weather_todo_project')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# Scheduled tasks
app.conf.beat_schedule = {
    'send-task-reminders': {
        'task': 'todo.tasks.send_task_reminders',
        'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
    },
}