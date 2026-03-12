from celery.schedules import crontab

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_celery_beat",
    "todo",
]

CELERY_BROKER_URL = "redis://127.0.0.1:6379/0"
CELERY_RESULT_BACKEND = "redis://127.0.0.1:6379/1"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# quick test schedule
CELERY_BEAT_SCHEDULE = {
    "debug-beat-every-minute": {
        "task": "todo.tasks.debug_beat_task",
        "schedule": crontab(minute="*/1"),
    }
}

OPENWEATHER_API_KEY = "your_api_key_here"