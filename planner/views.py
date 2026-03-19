import calendar
from collections import defaultdict
from datetime import date, timedelta
from uuid import uuid4

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import CreateView

from .forms import SignUpForm, TaskAttachmentForm, TaskForm, TaskShareForm
from .models import Task, TaskAttachment, TaskRecurrence, TaskShare, TaskShareStatus, TaskStatus

GEOCODING_URL = 'https://geocoding-api.open-meteo.com/v1/search'
WEATHER_URL = 'https://api.open-meteo.com/v1/forecast'


def home(request):
    if request.user.is_authenticated:
        return redirect('planner:dashboard')
    return redirect('login')


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('planner:dashboard')

    def form_valid(self, form):
        response = super().form_valid(form)
        email = self.object.email.lower().strip()
        TaskShare.objects.filter(recipient__isnull=True, recipient_email=email).update(
            recipient=self.object,
        )
        login(self.request, self.object)
        messages.success(self.request, 'Your account has been created successfully. Welcome!')
        return response


def task_queryset_for_user(user):
    return (
        Task.objects.filter(
            Q(owner=user) | Q(shares__recipient=user, shares__status=TaskShareStatus.ACCEPTED)
        )
        .select_related('owner')
        .prefetch_related('shares__recipient', 'attachments')
        .distinct()
    )


def get_editable_task(user, task_id):
    task = get_object_or_404(task_queryset_for_user(user), id=task_id)
    if task.owner_id == user.id:
        return task

    share = task.shares.filter(recipient=user).first()
    if share and share.status == TaskShareStatus.ACCEPTED and share.can_edit:
        return task

    raise Http404('Task not found')


def decorate_task_permissions(tasks, user):
    for task in tasks:
        task.user_is_owner = task.owner_id == user.id
        task.user_can_edit = task.user_is_owner or any(
            share.recipient_id == user.id and share.status == TaskShareStatus.ACCEPTED and share.can_edit
            for share in task.shares.all()
        )
    return tasks


def add_months(source_date, month_delta):
    target_month = source_date.month - 1 + month_delta
    target_year = source_date.year + target_month // 12
    target_month = target_month % 12 + 1
    day = min(source_date.day, calendar.monthrange(target_year, target_month)[1])
    return date(target_year, target_month, day)


def recurrence_dates(task):
    if task.recurrence == TaskRecurrence.NONE or not task.recurrence_ends_on:
        return []

    occurrence_dates = []
    next_date = task.scheduled_for
    while True:
        if task.recurrence == TaskRecurrence.DAILY:
            next_date = next_date + timedelta(days=1)
        elif task.recurrence == TaskRecurrence.WEEKLY:
            next_date = next_date + timedelta(days=7)
        elif task.recurrence == TaskRecurrence.MONTHLY:
            next_date = add_months(next_date, 1)
        elif task.recurrence == TaskRecurrence.YEARLY:
            next_date = add_months(next_date, 12)
        else:
            break

        if next_date > task.recurrence_ends_on:
            break
        occurrence_dates.append(next_date)

    return occurrence_dates


def sync_recurrence_series(task, create_series=True):
    if task.recurrence == TaskRecurrence.NONE or not task.recurrence_ends_on or not create_series:
        if task.recurrence_series:
            Task.objects.filter(
                recurrence_series=task.recurrence_series,
                owner=task.owner,
                is_recurring_generated=True,
            ).delete()
            task.recurrence_series = ''
            task.is_recurring_generated = False
            task.save(update_fields=['recurrence_series', 'is_recurring_generated', 'updated_at'])
        return

    if not task.recurrence_series:
        task.recurrence_series = str(uuid4())
        task.save(update_fields=['recurrence_series', 'updated_at'])

    Task.objects.filter(
        recurrence_series=task.recurrence_series,
        owner=task.owner,
        is_recurring_generated=True,
    ).delete()

    for scheduled_date in recurrence_dates(task):
        Task.objects.create(
            owner=task.owner,
            title=task.title,
            description=task.description,
            category=task.category,
            status=task.status,
            scheduled_for=scheduled_date,
            due_time=task.due_time,
            recurrence=task.recurrence,
            recurrence_ends_on=task.recurrence_ends_on,
            recurrence_series=task.recurrence_series,
            is_recurring_generated=True,
            reminder_enabled=task.reminder_enabled,
        )


def build_calendar_context(user, year, month):
    month_matrix = calendar.Calendar(firstweekday=6).monthdatescalendar(year, month)
    month_start = month_matrix[0][0]
    month_end = month_matrix[-1][-1]
    tasks = list(task_queryset_for_user(user).filter(scheduled_for__range=(month_start, month_end)))
    decorate_task_permissions(tasks, user)

    tasks_by_day = defaultdict(list)
    for task in tasks:
        tasks_by_day[task.scheduled_for].append(task)

    today = timezone.localdate()
    weeks = []
    for week in month_matrix:
        week_cells = []
        for day in week:
            week_cells.append(
                {
                    'date': day,
                    'in_month': day.month == month,
                    'is_today': day == today,
                    'tasks': tasks_by_day.get(day, []),
                }
            )
        weeks.append(week_cells)

    previous_month = month - 1 or 12
    previous_year = year - 1 if month == 1 else year
    next_month = 1 if month == 12 else month + 1
    next_year = year + 1 if month == 12 else year

    return {
        'calendar_weeks': weeks,
        'calendar_year': year,
        'calendar_month': month,
        'month_label': date(year, month, 1).strftime('%B %Y'),
        'previous_month': previous_month,
        'previous_year': previous_year,
        'next_month': next_month,
        'next_year': next_year,
    }


def weather_code_to_condition(code):
    if code == 0:
        return 'clear', 'Clear skies'
    if code in {1, 2, 3}:
        return 'cloudy', 'Cloud cover'
    if code in {45, 48}:
        return 'mist', 'Mist'
    if code in {71, 73, 75, 77, 85, 86}:
        return 'snow', 'Snow'
    if code in {95, 96, 99}:
        return 'storm', 'Thunderstorm'
    return 'rain', 'Rain'


@require_GET
def city_search(request):
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})

    try:
        response = requests.get(
            GEOCODING_URL,
            params={'name': query, 'count': 12, 'language': 'en', 'format': 'json'},
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException:
        return JsonResponse({'results': [], 'error': 'City search is unavailable right now.'}, status=502)

    payload = response.json()
    results = []
    for item in payload.get('results', []):
        results.append(
            {
                'name': item['name'],
                'country': item.get('country', ''),
                'admin1': item.get('admin1', ''),
                'latitude': item['latitude'],
                'longitude': item['longitude'],
                'label': ', '.join(part for part in [item['name'], item.get('admin1'), item.get('country')] if part),
            }
        )
    return JsonResponse({'results': results})


@require_GET
def weather_lookup(request):
    latitude = request.GET.get('lat')
    longitude = request.GET.get('lon')
    city_name = request.GET.get('name', 'Selected city')
    country = request.GET.get('country', '')
    if not latitude or not longitude:
        return JsonResponse({'error': 'Latitude and longitude are required.'}, status=400)

    try:
        response = requests.get(
            WEATHER_URL,
            params={
                'latitude': latitude,
                'longitude': longitude,
                'current': 'temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,is_day',
                'daily': 'weather_code,temperature_2m_max,temperature_2m_min',
                'forecast_days': 4,
                'timezone': 'auto',
            },
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException:
        return JsonResponse({'error': 'Weather data is unavailable right now.'}, status=502)

    payload = response.json()
    current = payload.get('current', {})
    condition, description = weather_code_to_condition(current.get('weather_code', 0))
    daily = payload.get('daily', {})
    forecast = []
    for index, day_value in enumerate(daily.get('time', [])[:4]):
        daily_condition, daily_description = weather_code_to_condition(daily.get('weather_code', [0])[index])
        forecast.append(
            {
                'date': day_value,
                'condition': daily_condition,
                'description': daily_description,
                'high': daily.get('temperature_2m_max', [None])[index],
                'low': daily.get('temperature_2m_min', [None])[index],
            }
        )

    return JsonResponse(
        {
            'city': city_name,
            'country': country,
            'condition': condition,
            'description': description,
            'temperature': current.get('temperature_2m'),
            'feels_like': current.get('apparent_temperature'),
            'humidity': current.get('relative_humidity_2m'),
            'wind_speed': current.get('wind_speed_10m'),
            'is_day': bool(current.get('is_day', 1)),
            'forecast': forecast,
        }
    )


@login_required
def dashboard(request):
    today = timezone.localdate()
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
    except ValueError:
        year = today.year
        month = today.month
    month = max(1, min(month, 12))
    _, month_days = calendar.monthrange(year, month)
    default_day = today.day if today.year == year and today.month == month else 1
    try:
        day = int(request.GET.get('day', default_day))
    except ValueError:
        day = default_day
    day = max(1, min(day, month_days))
    selected_date = date(year, month, day)

    visible_tasks = list(task_queryset_for_user(request.user))
    decorate_task_permissions(visible_tasks, request.user)
    selected_tasks = [task for task in visible_tasks if task.scheduled_for == selected_date]
    upcoming_tasks = [
        task for task in visible_tasks if task.scheduled_for >= today and task.status == TaskStatus.IN_PROGRESS
    ][:8]

    context = {
        'task_form': TaskForm(initial={'scheduled_for': selected_date}),
        'attachment_form': TaskAttachmentForm(),
        'share_form': TaskShareForm(),
        'selected_date': selected_date,
        'selected_tasks': selected_tasks,
        'upcoming_tasks': upcoming_tasks,
        'categories': Task._meta.get_field('category').choices,
        'recurrences': Task._meta.get_field('recurrence').choices,
        'received_invites': TaskShare.objects.filter(
            status=TaskShareStatus.PENDING,
            recipient=request.user,
        ).select_related('task', 'sender')[:6],
        'sent_pending_invites': TaskShare.objects.filter(
            sender=request.user,
            status=TaskShareStatus.PENDING,
        ).select_related('task', 'recipient')[:6],
    }
    context.update(build_calendar_context(request.user, year, month))
    return render(request, 'planner/dashboard.html', context)


@login_required
@require_POST
def create_task(request):
    form = TaskForm(request.POST)
    if form.is_valid():
        task = form.save(commit=False)
        task.owner = request.user
        task.save()
        create_series = bool(request.POST.get('create_series'))
        sync_recurrence_series(task, create_series=create_series)
        messages.success(request, 'Task has been created successfully.')
    else:
        messages.error(request, 'Task could not be created. Check the form fields.')
    return redirect('planner:dashboard')


@login_required
@require_POST
def update_task(request, task_id):
    task = get_editable_task(request.user, task_id)
    form = TaskForm(request.POST, instance=task)
    if form.is_valid():
        apply_scope = request.POST.get('apply_scope', 'single')
        if apply_scope == 'series' and task.recurrence_series and task.owner_id == request.user.id:
            base_task = (
                Task.objects.filter(
                    owner=request.user,
                    recurrence_series=task.recurrence_series,
                    is_recurring_generated=False,
                )
                .order_by('scheduled_for')
                .first()
            )
            if not base_task:
                base_task = task
            for field, value in form.cleaned_data.items():
                if hasattr(base_task, field):
                    setattr(base_task, field, value)
            base_task.is_recurring_generated = False
            base_task.save()
            sync_recurrence_series(base_task, create_series=bool(request.POST.get('create_series')))
        else:
            updated_task = form.save()
            sync_recurrence_series(updated_task, create_series=bool(request.POST.get('create_series')))
        messages.success(request, 'Task has been edited successfully.')
    else:
        messages.error(request, 'Task could not be updated.')
    return redirect('planner:dashboard')


@login_required
@require_POST
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, owner=request.user)
    delete_scope = request.POST.get('delete_scope', 'single')
    if delete_scope == 'series' and task.recurrence_series:
        Task.objects.filter(owner=request.user, recurrence_series=task.recurrence_series).delete()
    else:
        task.delete()
    messages.success(request, 'Task has been deleted successfully.')
    return redirect('planner:dashboard')


@login_required
@require_POST
def toggle_task_status(request, task_id):
    task = get_editable_task(request.user, task_id)
    task.status = TaskStatus.DONE if task.status == TaskStatus.IN_PROGRESS else TaskStatus.IN_PROGRESS
    task.save(update_fields=['status', 'updated_at'])
    messages.success(request, 'Task status updated.')
    return redirect('planner:dashboard')


@login_required
@require_POST
def share_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, owner=request.user)
    form = TaskShareForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Share request could not be processed.')
        return redirect('planner:dashboard')

    recipient_email = form.cleaned_data['recipient_email'].lower().strip()
    if recipient_email == request.user.email.lower().strip():
        messages.error(request, 'You cannot share a task with yourself.')
        return redirect('planner:dashboard')

    recipient = User.objects.filter(email__iexact=recipient_email).first()
    share, _ = TaskShare.objects.update_or_create(
        task=task,
        recipient_email=recipient_email,
        defaults={
            'sender': request.user,
            'recipient': recipient,
            'can_edit': form.cleaned_data['can_edit'],
            'message': form.cleaned_data.get('message', ''),
            'status': TaskShareStatus.PENDING,
            'accepted_at': None,
            'responded_at': None,
        },
    )
    invite_link = request.build_absolute_uri(reverse('planner:invite_detail', args=[share.invite_token]))
    permission_label = 'can edit' if share.can_edit else 'can view'
    message_body = (
        f'{request.user.username} shared "{task.title}" scheduled for {task.scheduled_for:%Y-%m-%d}.\n\n'
        f'Permission: {permission_label}\n'
        f'Invitation link: {invite_link}\n\n'
    )
    if share.message:
        message_body += f'Message from sender:\n{share.message}\n\n'
    message_body += 'Sign in and accept the invite to access the task.'
    send_mail(
        f'{request.user.username} invited you to a shared task',
        message_body,
        settings.DEFAULT_FROM_EMAIL,
        [share.recipient_email],
        fail_silently=True,
    )
    messages.success(request, f'Task shared with {share.recipient_email}.')
    return redirect('planner:dashboard')


@login_required
@require_POST
def upload_attachment(request, task_id):
    task = get_editable_task(request.user, task_id)
    form = TaskAttachmentForm(request.POST, request.FILES)
    if form.is_valid() and request.FILES.get('file'):
        attachment = form.save(commit=False)
        attachment.task = task
        attachment.uploaded_by = request.user
        attachment.save()
        messages.success(request, 'Attachment uploaded.')
    else:
        messages.error(request, 'Attachment could not be uploaded.')
    return redirect('planner:dashboard')


@login_required
@require_POST
def delete_attachment(request, attachment_id):
    attachment = get_object_or_404(TaskAttachment, id=attachment_id)
    task = get_editable_task(request.user, attachment.task_id)
    if task.id != attachment.task_id:
        raise Http404('Attachment not found')
    attachment.file.delete(save=False)
    attachment.delete()
    messages.success(request, 'Attachment removed.')
    return redirect('planner:dashboard')


@login_required
def invite_detail(request, token):
    share = get_object_or_404(TaskShare.objects.select_related('task', 'sender', 'recipient'), invite_token=token)
    if request.user.email.lower().strip() != share.recipient_email:
        messages.error(request, 'This invite is linked to a different email address.')
        return redirect('planner:dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'accept':
            share.recipient = request.user
            share.status = TaskShareStatus.ACCEPTED
            share.accepted_at = timezone.now()
            share.responded_at = timezone.now()
            share.save(update_fields=['recipient', 'status', 'accepted_at', 'responded_at'])
            messages.success(request, 'Invite accepted. Task is now in your dashboard.')
        elif action == 'decline':
            share.recipient = request.user
            share.status = TaskShareStatus.DECLINED
            share.responded_at = timezone.now()
            share.save(update_fields=['recipient', 'status', 'responded_at'])
            messages.success(request, 'Invite declined.')
        return redirect('planner:dashboard')

    return render(request, 'planner/invite_detail.html', {'share': share})


@login_required
@require_POST
def accept_invite(request, share_id):
    share = get_object_or_404(TaskShare, id=share_id, status=TaskShareStatus.PENDING)
    if request.user.email.lower().strip() != share.recipient_email:
        raise Http404('Invite not found')
    share.recipient = request.user
    share.status = TaskShareStatus.ACCEPTED
    share.accepted_at = timezone.now()
    share.responded_at = timezone.now()
    share.save(update_fields=['recipient', 'status', 'accepted_at', 'responded_at'])
    messages.success(request, 'Invite accepted.')
    return redirect('planner:dashboard')


@login_required
@require_POST
def decline_invite(request, share_id):
    share = get_object_or_404(TaskShare, id=share_id, status=TaskShareStatus.PENDING)
    if request.user.email.lower().strip() != share.recipient_email:
        raise Http404('Invite not found')
    share.recipient = request.user
    share.status = TaskShareStatus.DECLINED
    share.responded_at = timezone.now()
    share.save(update_fields=['recipient', 'status', 'responded_at'])
    messages.success(request, 'Invite declined.')
    return redirect('planner:dashboard')


@login_required
@require_POST
def revoke_invite(request, share_id):
    share = get_object_or_404(TaskShare, id=share_id, sender=request.user, status=TaskShareStatus.PENDING)
    share.status = TaskShareStatus.REVOKED
    share.responded_at = timezone.now()
    share.save(update_fields=['status', 'responded_at'])
    messages.success(request, 'Invite revoked.')
    return redirect('planner:dashboard')
# Create your views here.
