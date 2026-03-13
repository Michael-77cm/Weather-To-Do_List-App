from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.db.models import Q
from django.urls import reverse
from .models import Task, TaskCategory, SharedTask
from .forms import TaskForm, ShareTaskForm
from datetime import datetime

@login_required
def task_list(request):
    """View for listing all tasks"""
    tasks = Task.objects.filter(
        Q(created_by=request.user) | Q(assigned_to=request.user)
    ).distinct()
    
    # Filter by status
    status_filter = request.GET.get('status', 'all')
    if status_filter == 'in_progress':
        tasks = tasks.filter(status='in_progress')
    elif status_filter == 'completed':
        tasks = tasks.filter(status='completed')
    
    # Filter by category
    category_filter = request.GET.get('category', 'all')
    if category_filter != 'all':
        tasks = tasks.filter(category__name=category_filter)
    
    context = {
        'tasks': tasks,
        'categories': TaskCategory.objects.all(),
        'current_status': status_filter,
        'current_category': category_filter,
    }
    return render(request, 'todo/task_list.html', context)

@login_required
def task_detail(request, pk):
    """View for task details"""
    task = get_object_or_404(Task, pk=pk)
    
    # Check permission
    if request.user != task.created_by and request.user not in task.assigned_to.all():
        messages.error(request, "You don't have permission to view this task.")
        return redirect('todo:task_list')
    
    if request.method == 'POST' and 'share_task' in request.POST:
        share_form = ShareTaskForm(request.POST)
        if share_form.is_valid():
            email = share_form.cleaned_data['email']
            message = share_form.cleaned_data['message']
            
            # Create shared task record
            shared_task, created = SharedTask.objects.get_or_create(
                task=task,
                shared_by=request.user,
                shared_with_email=email
            )
            
            if created:
                # Send email notification
                send_task_share_email(request.user, email, task, message)
                messages.success(request, f'Task shared with {email}')
            else:
                messages.info(request, f'Task already shared with {email}')
    
    context = {
        'task': task,
        'share_form': ShareTaskForm(),
    }
    return render(request, 'todo/task_detail.html', context)

@login_required
def task_create(request):
    """View for creating a new task"""
    if request.method == 'POST':
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            form.save_m2m()  # Save many-to-many relationships
            
            messages.success(request, 'Task created successfully!')
            return redirect('todo:task_detail', pk=task.pk)
    else:
        form = TaskForm(user=request.user)
    
    return render(request, 'todo/task_form.html', {'form': form, 'title': 'Create Task'})

@login_required
def task_update(request, pk):
    """View for updating a task"""
    task = get_object_or_404(Task, pk=pk)
    
    # Check permission (only creator can update)
    if request.user != task.created_by:
        messages.error(request, "You don't have permission to edit this task.")
        return redirect('todo:task_detail', pk=task.pk)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task updated successfully!')
            return redirect('todo:task_detail', pk=task.pk)
    else:
        form = TaskForm(instance=task, user=request.user)
    
    return render(request, 'todo/task_form.html', {'form': form, 'title': 'Update Task'})

@login_required
def task_delete(request, pk):
    """View for deleting a task"""
    task = get_object_or_404(Task, pk=pk)
    
    # Check permission (only creator can delete)
    if request.user != task.created_by:
        messages.error(request, "You don't have permission to delete this task.")
        return redirect('todo:task_list')
    
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted successfully!')
        return redirect('todo:task_list')
    
    return render(request, 'todo/task_confirm_delete.html', {'task': task})

@login_required
@require_http_methods(['POST'])
def task_mark_completed(request, pk):
    """AJAX endpoint to mark task as completed"""
    task = get_object_or_404(Task, pk=pk)
    
    # Check permission
    if request.user != task.created_by and request.user not in task.assigned_to.all():
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    task.mark_completed()
    
    return JsonResponse({
        'success': True,
        'status': task.status,
        'completed_at': task.completed_at.strftime('%Y-%m-%d %H:%M') if task.completed_at else None
    })

@login_required
def calendar_view(request):
    """View for calendar with tasks"""
    return render(request, 'todo/calendar.html')

@login_required
def get_calendar_tasks(request):
    """AJAX endpoint to get tasks for calendar"""
    year = int(request.GET.get('year', datetime.now().year))
    month = int(request.GET.get('month', datetime.now().month))
    
    tasks = Task.objects.filter(
        Q(created_by=request.user) | Q(assigned_to=request.user),
        due_date__year=year,
        due_date__month=month
    ).distinct()
    
    events = []
    for task in tasks:
        events.append({
            'id': task.id,
            'title': task.title,
            'start': task.due_date.isoformat(),
            'description': task.description,
            'status': task.status,
            'category': task.category.name if task.category else 'uncategorized',
            'priority': task.priority,
            'url': reverse('todo:task_detail', args=[task.id])
        })
    
    return JsonResponse(events, safe=False)

def send_task_share_email(sharer, recipient_email, task, message):
    """Helper function to send task sharing email"""
    subject = f"{sharer.username} shared a task with you: {task.title}"
    
    html_message = render_to_string('todo/email/share_task.html', {
        'sharer': sharer,
        'task': task,
        'message': message,
        'site_url': settings.SITE_URL
    })
    
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [recipient_email],
        html_message=html_message,
        fail_silently=False,
    )