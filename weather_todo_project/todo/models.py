from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class TaskCategory(models.Model):
    CATEGORY_CHOICES = [
        ('work', 'Work'),
        ('personal', 'Personal'),
        ('shopping', 'Shopping'),
        ('business', 'Business'),
        ('wishlist', 'Wish List'),
    ]
    
    name = models.CharField(max_length=20, choices=CATEGORY_CHOICES, unique=True)
    
    def __str__(self):
        return self.get_name_display()
    
    class Meta:
        verbose_name_plural = "Task Categories"

class Task(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(TaskCategory, on_delete=models.SET_NULL, null=True, related_name='tasks')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    assigned_to = models.ManyToManyField(User, related_name='assigned_tasks', blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    due_date = models.DateField(null=True, blank=True)
    due_time = models.TimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-priority', 'due_date', 'created_at']
    
    def __str__(self):
        return self.title
    
    def mark_completed(self):
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()

class SharedTask(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='shared_with')
    shared_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_tasks')
    shared_with_email = models.EmailField()
    shared_at = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['task', 'shared_with_email']
    
    def __str__(self):
        return f"{self.task.title} shared with {self.shared_with_email}"