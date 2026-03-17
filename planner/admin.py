from django.contrib import admin

from .models import Task, TaskAttachment, TaskShare


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'category', 'status', 'scheduled_for', 'recurrence', 'reminder_enabled')
    list_filter = ('category', 'status', 'recurrence', 'reminder_enabled', 'scheduled_for')
    search_fields = ('title', 'description', 'owner__username', 'owner__email')


@admin.register(TaskShare)
class TaskShareAdmin(admin.ModelAdmin):
    list_display = ('task', 'sender', 'recipient_email', 'recipient', 'status', 'can_edit', 'created_at')
    list_filter = ('status', 'can_edit', 'created_at')
    search_fields = ('task__title', 'recipient_email', 'sender__username', 'recipient__username')


@admin.register(TaskAttachment)
class TaskAttachmentAdmin(admin.ModelAdmin):
    list_display = ('task', 'name', 'uploaded_by', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('task__title', 'name', 'uploaded_by__username')