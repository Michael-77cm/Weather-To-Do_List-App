from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from functools import wraps
from .models import TaskShare

def has_task_permission(permission_required='view'):
    """
    Decorator to check if user has permission to access a task.
    permission_required can be 'view', 'edit', or 'admin'
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, todo_id, *args, **kwargs):
            from .models import TodoItem
            
            try:
                task = TodoItem.objects.get(id=todo_id)
            except TodoItem.DoesNotExist:
                messages.error(request, 'Task not found.')
                return redirect('index')
            
            # Task owner has full access
            if task.user == request.user:
                return view_func(request, todo_id, *args, **kwargs)
            
            # Check if task is shared with user
            try:
                share = TaskShare.objects.get(
                    task=task,
                    shared_with=request.user,
                    is_active=True
                )
                
                # Check permission level
                if permission_required == 'view':
                    return view_func(request, todo_id, *args, **kwargs)
                elif permission_required == 'edit' and share.permission in ['edit', 'admin']:
                    return view_func(request, todo_id, *args, **kwargs)
                elif permission_required == 'admin' and share.permission == 'admin':
                    return view_func(request, todo_id, *args, **kwargs)
                
            except TaskShare.DoesNotExist:
                pass
            
            raise PermissionDenied("You don't have permission to access this task.")
        
        return _wrapped_view
    
    return decorator

def ajax_required(view_func):
    """Decorator to ensure request is AJAX"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            messages.error(request, 'This action requires AJAX request.')
            return redirect('index')
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view