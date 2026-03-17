import os
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class TaskCategory(models.TextChoices):
    WORK = 'work', 'Work'
    PERSONAL = 'personal', 'Personal'
    SHOPPING = 'shopping', 'Shopping'
    BUSINESS = 'business', 'Business'
    WISH_LIST = 'wish_list', 'Wish List'


class TaskStatus(models.TextChoices):
    IN_PROGRESS = 'in_progress', 'In Progress'
    DONE = 'done', 'Done'


class TaskRecurrence(models.TextChoices):
    NONE = 'none', 'Does Not Repeat'
    DAILY = 'daily', 'Daily'
    WEEKLY = 'weekly', 'Weekly'
    MONTHLY = 'monthly', 'Monthly'
    YEARLY = 'yearly', 'Yearly'


class Task(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_tasks')
    title = models.CharField(max_length=140)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=TaskCategory.choices, default=TaskCategory.PERSONAL)
    status = models.CharField(max_length=20, choices=TaskStatus.choices, default=TaskStatus.IN_PROGRESS)
    scheduled_for = models.DateField()
    due_time = models.TimeField(blank=True, null=True)
    recurrence = models.CharField(max_length=20, choices=TaskRecurrence.choices, default=TaskRecurrence.NONE)
    recurrence_ends_on = models.DateField(blank=True, null=True)
    recurrence_series = models.CharField(max_length=36, blank=True, db_index=True)
    is_recurring_generated = models.BooleanField(default=False)
    reminder_enabled = models.BooleanField(default=True)
    last_reminder_sent_on = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['scheduled_for', 'due_time', 'title']

    def __str__(self):
        return f'{self.title} ({self.scheduled_for})'

    @property
    def is_done(self):
        return self.status == TaskStatus.DONE

    @property
    def is_recurring(self):
        return self.recurrence != TaskRecurrence.NONE


class TaskShareStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    ACCEPTED = 'accepted', 'Accepted'
    DECLINED = 'declined', 'Declined'
    REVOKED = 'revoked', 'Revoked'


class TaskShare(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='shares')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_task_shares')
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='received_task_shares',
    )
    recipient_email = models.EmailField()
    can_edit = models.BooleanField(default=True)
    status = models.CharField(max_length=16, choices=TaskShareStatus.choices, default=TaskShareStatus.PENDING)
    message = models.TextField(blank=True)
    invite_token = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    accepted_at = models.DateTimeField(blank=True, null=True)
    responded_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['task', 'recipient_email'], name='unique_task_recipient_email'),
        ]

    def __str__(self):
        return f'{self.task.title} -> {self.recipient_email}'

    def save(self, *args, **kwargs):
        self.recipient_email = self.recipient_email.lower().strip()
        if self.status == TaskShareStatus.ACCEPTED and not self.accepted_at:
            self.accepted_at = timezone.now()
        super().save(*args, **kwargs)


class TaskAttachment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='task_attachments',
    )
    file = models.FileField(upload_to='task_attachments/%Y/%m/%d')
    name = models.CharField(max_length=140, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.name or os.path.basename(self.file.name)

    def save(self, *args, **kwargs):
        if not self.name and self.file:
            self.name = os.path.basename(self.file.name)
        super().save(*args, **kwargs)

# Create your models here.
