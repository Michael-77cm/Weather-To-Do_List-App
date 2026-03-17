from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone

from planner.models import Task, TaskStatus


class Command(BaseCommand):
    help = 'Email reminders for tasks scheduled for a future day.'

    def add_arguments(self, parser):
        parser.add_argument('--days-ahead', type=int, default=1, help='Send reminders for tasks due N days ahead.')

    def handle(self, *args, **options):
        today = timezone.localdate()
        target_date = today + timedelta(days=options['days_ahead'])
        tasks = Task.objects.filter(
            scheduled_for=target_date,
            status=TaskStatus.IN_PROGRESS,
            reminder_enabled=True,
        ).select_related('owner')

        sent_count = 0
        for task in tasks:
            if task.last_reminder_sent_on == today:
                continue

            recipients = {task.owner.email}
            recipients.update(task.shares.exclude(recipient_email='').values_list('recipient_email', flat=True))
            recipients.discard('')
            if not recipients:
                continue

            send_mail(
                f'Reminder: {task.title}',
                (
                    f'Your task "{task.title}" is scheduled for {task.scheduled_for:%Y-%m-%d}.\n\n'
                    f'Category: {task.get_category_display()}\n'
                    f'Status: {task.get_status_display()}'
                ),
                settings.DEFAULT_FROM_EMAIL,
                sorted(recipients),
                fail_silently=True,
            )
            task.last_reminder_sent_on = today
            task.save(update_fields=['last_reminder_sent_on', 'updated_at'])
            sent_count += 1

        self.stdout.write(self.style.SUCCESS(f'Sent {sent_count} reminder(s) for {target_date:%Y-%m-%d}.'))