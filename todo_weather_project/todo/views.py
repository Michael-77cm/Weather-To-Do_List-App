from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import TodoItem, UserProfile, TaskShare, TaskComment, TaskHistory, Notification
from .forms import (UserRegistrationForm, UserLoginForm, EnhancedTodoForm, 
                   UserProfileForm, UserUpdateForm, TaskShareForm, 
                   TaskCommentForm, TaskFilterForm)
from .decorators import has_task_permission
from .utils import create_notification
import json
from datetime import datetime, timedelta

# ==================== AUTHENTICATION VIEWS ====================

def register_view(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Create user profile
            UserProfile.objects.create(user=user)
            
            # Send welcome email
            send_welcome_email(user)
            
            # Log the user in
            login(request, user)
            messages.success(request, f'Welcome {user.username}! Your account has been created successfully.')
            
            # Create welcome notification
            create_notification(
                user=user,
                type='system',
                title='Welcome to Todo & Weather App!',
                message='We\'re excited to have you on board. Start by creating your first task.'
            )
            
            return redirect('index')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'todo/registration/register.html', {'form': form})

def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                
                # Update last login notification
                create_notification(
                    user=user,
                    type='system',
                    title='Successful Login',
                    message=f'You logged in at {timezone.now().strftime("%Y-%m-%d %H:%M")}'
                )
                
                return redirect('index')
    else:
        form = UserLoginForm()
    
    return render(request, 'todo/registration/login.html', {'form': form})

@login_required
def logout_view(request):
    """User logout view"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')

@login_required
def profile_view(request):
    """User profile view"""
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = UserProfileForm(instance=profile)
    
    # Get user statistics
    total_tasks = TodoItem.objects.filter(user=user).count()
    completed_tasks = TodoItem.objects.filter(user=user, completed=True).count()
    pending_tasks = total_tasks - completed_tasks
    shared_tasks = TaskShare.objects.filter(shared_with=user).count()
    
    # Get recent activity
    recent_activity = TaskHistory.objects.filter(user=user)[:10]
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'shared_tasks': shared_tasks,
        'recent_activity': recent_activity,
    }
    return render(request, 'todo/registration/profile.html', context)

# ==================== TODO VIEWS ====================

@login_required
def index(request):
    """Main view for todo list with filtering and pagination"""
    user = request.user
    filter_form = TaskFilterForm(request.GET)
    
    # Base queryset
    # Get user's own tasks and tasks shared with them
    own_tasks = TodoItem.objects.filter(user=user)
    shared_tasks = TodoItem.objects.filter(
        shares__shared_with=user,
        shares__is_active=True
    ).distinct()
    
    todos = own_tasks | shared_tasks
    
    # Apply filters
    if filter_form.is_valid():
        search = filter_form.cleaned_data.get('search')
        status = filter_form.cleaned_data.get('status')
        priority = filter_form.cleaned_data.get('priority')
        category = filter_form.cleaned_data.get('category')
        tag = filter_form.cleaned_data.get('tag')
        
        if search:
            todos = todos.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search)
            )
        
        if status == 'active':
            todos = todos.filter(completed=False)
        elif status == 'completed':
            todos = todos.filter(completed=True)
        elif status == 'overdue':
            todos = todos.filter(
                completed=False,
                due_date__lt=timezone.now()
            )
        
        if priority:
            todos = todos.filter(priority=priority)
        
        if category:
            todos = todos.filter(category=category)
        
        if tag:
            todos = todos.filter(tags__icontains=tag)
    
    # Pagination
    paginator = Paginator(todos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Separate active and completed
    active_todos = [todo for todo in page_obj if not todo.completed]
    completed_todos = [todo for todo in page_obj if todo.completed]
    
    # Statistics
    total_todos = todos.count()
    completed_count = todos.filter(completed=True).count()
    pending_count = total_todos - completed_count
    
    # Get unread notifications count
    unread_notifications = Notification.objects.filter(user=user, is_read=False).count()
    
    # Get shared tasks count
    shared_with_me_count = TaskShare.objects.filter(
        shared_with=user,
        is_active=True
    ).count()
    
    context = {
        'page_obj': page_obj,
        'active_todos': active_todos,
        'completed_todos': completed_todos,
        'total_todos': total_todos,
        'completed_count': completed_count,
        'pending_count': pending_count,
        'filter_form': filter_form,
        'unread_notifications': unread_notifications,
        'shared_with_me_count': shared_with_me_count,
        'now': timezone.now(),
    }
    return render(request, 'todo/index.html', context)

@login_required
def add_todo(request):
    """Add a new todo item"""
    if request.method == 'POST':
        form = EnhancedTodoForm(request.POST, request.FILES)
        if form.is_valid():
            todo = form.save(commit=False)
            todo.user = request.user
            todo.save()
            
            # Create history entry
            TaskHistory.objects.create(
                task=todo,
                user=request.user,
                action='create',
                details={'title': todo.title}
            )
            
            messages.success(request, 'Task created successfully!')
            return redirect('index')
    else:
        form = EnhancedTodoForm()
    
    return render(request, 'todo/add_todo.html', {'form': form})

@login_required
@has_task_permission(permission_required='edit')
def edit_todo(request, todo_id):
    """Edit an existing todo item"""
    todo = get_object_or_404(TodoItem, id=todo_id)
    
    if request.method == 'POST':
        form = EnhancedTodoForm(request.POST, request.FILES, instance=todo)
        if form.is_valid():
            form.save()
            
            # Create history entry
            TaskHistory.objects.create(
                task=todo,
                user=request.user,
                action='update',
                details={'changes': 'Task updated'}
            )
            
            messages.success(request, 'Task updated successfully!')
            return redirect('index')
    else:
        form = EnhancedTodoForm(instance=todo)
    
    return render(request, 'todo/edit_todo.html', {'form': form, 'todo': todo})

@login_required
@has_task_permission(permission_required='edit')
def delete_todo(request, todo_id):
    """Delete a todo item"""
    todo = get_object_or_404(TodoItem, id=todo_id)
    
    if request.method == 'POST':
        # Create history before deleting
        TaskHistory.objects.create(
            task=todo,
            user=request.user,
            action='delete',
            details={'title': todo.title}
        )
        
        todo.delete()
        messages.success(request, 'Task deleted successfully!')
        return redirect('index')
    
    return render(request, 'todo/delete_todo.html', {'todo': todo})

@login_required
@has_task_permission(permission_required='edit')
@require_http_methods(["POST"])
def toggle_complete(request, todo_id):
    """Toggle the completed status of a todo item"""
    try:
        todo = get_object_or_404(TodoItem, id=todo_id)
        todo.completed = not todo.completed
        todo.save()
        
        # Create history entry
        action = 'complete' if todo.completed else 'reopen'
        TaskHistory.objects.create(
            task=todo,
            user=request.user,
            action=action
        )
        
        # Create notification for task owner if different from completer
        if todo.user != request.user:
            create_notification(
                user=todo.user,
                type='complete',
                title=f'Task {"Completed" if todo.completed else "Reopened"}',
                message=f'{request.user.username} has {"completed" if todo.completed else "reopened"} your task: {todo.title}',
                task=todo
            )
        
        return JsonResponse({
            'success': True,
            'completed': todo.completed,
            'message': f'Task marked as {"completed" if todo.completed else "incomplete"}'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@login_required
def task_detail(request, todo_id):
    """View task details with comments and history"""
    todo = get_object_or_404(TodoItem, id=todo_id)
    
    # Check permission
    if todo.user != request.user and not TaskShare.objects.filter(
        task=todo, shared_with=request.user, is_active=True
    ).exists():
        return HttpResponseForbidden("You don't have permission to view this task.")
    
    # Get comments
    comments = TaskComment.objects.filter(task=todo)
    
    # Get history
    history = TaskHistory.objects.filter(task=todo)
    
    # Get shares
    shares = TaskShare.objects.filter(task=todo)
    
    if request.method == 'POST':
        comment_form = TaskCommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.task = todo
            comment.user = request.user
            comment.save()
            
            # Create notification for task owner
            if todo.user != request.user:
                create_notification(
                    user=todo.user,
                    type='comment',
                    title='New Comment',
                    message=f'{request.user.username} commented on your task: {todo.title}',
                    task=todo
                )
            
            messages.success(request, 'Comment added successfully!')
            return redirect('task_detail', todo_id=todo.id)
    else:
        comment_form = TaskCommentForm()
    
    context = {
        'todo': todo,
        'comments': comments,
        'history': history,
        'shares': shares,
        'comment_form': comment_form,
    }
    return render(request, 'todo/task_detail.html', context)

# ==================== SHARING VIEWS ====================

@login_required
def share_task(request, todo_id):
    """Share a task with another user"""
    todo = get_object_or_404(TodoItem, id=todo_id, user=request.user)
    
    if request.method == 'POST':
        form = TaskShareForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            shared_with = User.objects.get(email=email)
            permission = form.cleaned_data['permission']
            
            # Check if share already exists
            share, created = TaskShare.objects.get_or_create(
                task=todo,
                shared_with=shared_with,
                defaults={
                    'shared_by': request.user,
                    'permission': permission
                }
            )
            
            if not created:
                share.is_active = True
                share.permission = permission
                share.save()
                messages.info(request, f'Task already shared with {shared_with.username}. Permission updated.')
            else:
                messages.success(request, f'Task shared with {shared_with.username}!')
            
            # Create history entry
            TaskHistory.objects.create(
                task=todo,
                user=request.user,
                action='share',
                details={'shared_with': shared_with.username, 'permission': permission}
            )
            
            # Create notification for shared user
            create_notification(
                user=shared_with,
                type='share',
                title='Task Shared With You',
                message=f'{request.user.username} shared a task with you: {todo.title}',
                task=todo
            )
            
            # Send email notification
            send_task_shared_email(request.user, shared_with, todo, permission)
            
            return redirect('manage_shares', todo_id=todo.id)
    else:
        form = TaskShareForm()
    
    # Get existing shares
    shares = TaskShare.objects.filter(task=todo)
    
    context = {
        'todo': todo,
        'form': form,
        'shares': shares,
    }
    return render(request, 'todo/sharing/share_task.html', context)

@login_required
def manage_shares(request, todo_id):
    """Manage shares for a task"""
    todo = get_object_or_404(TodoItem, id=todo_id, user=request.user)
    shares = TaskShare.objects.filter(task=todo)
    
    if request.method == 'POST':
        share_id = request.POST.get('share_id')
        action = request.POST.get('action')
        
        share = get_object_or_404(TaskShare, id=share_id, task=todo)
        
        if action == 'remove':
            share.delete()
            messages.success(request, f'Share removed for {share.shared_with.username}')
        elif action == 'update':
            new_permission = request.POST.get('permission')
            share.permission = new_permission
            share.save()
            messages.success(request, f'Permission updated for {share.shared_with.username}')
        
        return redirect('manage_shares', todo_id=todo.id)
    
    context = {
        'todo': todo,
        'shares': shares,
    }
    return render(request, 'todo/sharing/manage_shares.html', context)

@login_required
def shared_with_me(request):
    """View tasks shared with the current user"""
    shared_tasks = TaskShare.objects.filter(
        shared_with=request.user,
        is_active=True
    ).select_related('task', 'shared_by')
    
    context = {
        'shared_tasks': shared_tasks,
    }
    return render(request, 'todo/sharing/shared_with_me.html', context)

@login_required
def accept_share(request, token):
    """Accept a shared task via token"""
    share = get_object_or_404(TaskShare, share_token=token)
    
    if share.shared_with != request.user:
        return HttpResponseForbidden("This share token is not for you.")
    
    share.is_active = True
    share.save()
    
    messages.success(request, f'You now have access to task: {share.task.title}')
    return redirect('task_detail', todo_id=share.task.id)

# ==================== NOTIFICATION VIEWS ====================

@login_required
def notifications(request):
    """View user notifications"""
    notifications = Notification.objects.filter(user=request.user)
    
    # Mark all as read if requested
    if request.GET.get('mark_read'):
        notifications.update(is_read=True, read_at=timezone.now())
        messages.success(request, 'All notifications marked as read')
        return redirect('notifications')
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'todo/notifications.html', context)

@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """Mark a single notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.mark_as_read()
    
    return JsonResponse({'success': True})

# ==================== WEATHER VIEW ====================

@login_required
def weather_view(request):
    """View for weather information"""
    weather_data = None
    forecast_data = None
    city = request.GET.get('city', request.user.profile.location or 'London')
    
    if city:
        try:
            api_key = settings.WEATHER_API_KEY
            
            # Current weather
            current_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
            current_response = requests.get(current_url)
            
            if current_response.status_code == 200:
                current_data = current_response.json()
                weather_data = {
                    'city': current_data['name'],
                    'country': current_data['sys']['country'],
                    'temperature': round(current_data['main']['temp']),
                    'feels_like': round(current_data['main']['feels_like']),
                    'temp_min': round(current_data['main']['temp_min']),
                    'temp_max': round(current_data['main']['temp_max']),
                    'description': current_data['weather'][0]['description'],
                    'icon': current_data['weather'][0]['icon'],
                    'humidity': current_data['main']['humidity'],
                    'wind_speed': current_data['wind']['speed'],
                    'pressure': current_data['main']['pressure'],
                    'visibility': current_data.get('visibility', 0) / 1000,
                    'sunrise': datetime.fromtimestamp(current_data['sys']['sunrise']).strftime('%H:%M'),
                    'sunset': datetime.fromtimestamp(current_data['sys']['sunset']).strftime('%H:%M'),
                }
                
                # 5-day forecast
                forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric"
                forecast_response = requests.get(forecast_url)
                
                if forecast_response.status_code == 200:
                    forecast_data = []
                    forecast_json = forecast_response.json()
                    
                    for item in forecast_json['list'][:5]:
                        forecast_data.append({
                            'date': datetime.strptime(item['dt_txt'], '%Y-%m-%d %H:%M:%S').strftime('%A'),
                            'temp': round(item['main']['temp']),
                            'description': item['weather'][0]['description'],
                            'icon': item['weather'][0]['icon'],
                        })
            else:
                messages.error(request, 'City not found. Please try again.')
        except Exception as e:
            messages.error(request, 'Error fetching weather data. Please try again.')
    
    return render(request, 'todo/weather.html', {
        'weather_data': weather_data,
        'forecast_data': forecast_data,
        'city': city
    })

# ==================== EMAIL FUNCTIONS ====================

def send_welcome_email(user):
    """Send welcome email to new user"""
    subject = 'Welcome to Todo & Weather App!'
    html_message = render_to_string('todo/emails/welcome_email.html', {'user': user})
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=True,
    )

def send_task_shared_email(shared_by, shared_with, task, permission):
    """Send email notification when task is shared"""
    subject = f'{shared_by.username} shared a task with you'
    html_message = render_to_string('todo/emails/task_shared.html', {
        'shared_by': shared_by,
        'shared_with': shared_with,
        'task': task,
        'permission': permission,
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [shared_with.email],
        html_message=html_message,
        fail_silently=True,
    )

def send_task_reminder_email(task):
    """Send reminder email for upcoming task"""
    user = task.user
    if not user.profile.email_notifications or not user.profile.task_reminders:
        return
    
    subject = f'Reminder: {task.title} is due soon'
    html_message = render_to_string('todo/emails/task_reminder.html', {
        'user': user,
        'task': task,
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=True,
    )

def send_daily_summary(user):
    """Send daily summary email"""
    if not user.profile.email_notifications or not user.profile.daily_summary:
        return
    
    # Get today's tasks
    today = timezone.now().date()
    tasks_due_today = TodoItem.objects.filter(
        user=user,
        due_date__date=today,
        completed=False
    )
    
    overdue_tasks = TodoItem.objects.filter(
        user=user,
        due_date__lt=timezone.now(),
        completed=False
    )
    
    completed_today = TodoItem.objects.filter(
        user=user,
        completed_date__date=today
    )
    
    subject = 'Your Daily Task Summary'
    html_message = render_to_string('todo/emails/daily_summary.html', {
        'user': user,
        'tasks_due_today': tasks_due_today,
        'overdue_tasks': overdue_tasks,
        'completed_today': completed_today,
        'date': today,
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=True,
    )