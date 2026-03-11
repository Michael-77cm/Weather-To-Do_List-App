from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import TodoItem, UserProfile, TaskComment, TaskShare
from django.utils import timezone
import re

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your email'
    }))
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'First name'
    }))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Last name'
    }))
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'location', 'birth_date', 'profile_picture', 
                 'theme_preference', 'email_notifications', 'task_reminders',
                 'daily_summary', 'weekly_report', 'auto_accept_shares']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'theme_preference': forms.Select(attrs={'class': 'form-control'}),
        }

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        username = self.cleaned_data.get('username')
        
        if email and User.objects.filter(email=email).exclude(username=username).exists():
            raise forms.ValidationError('This email is already in use.')
        return email

class EnhancedTodoForm(forms.ModelForm):
    tags = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter tags separated by commas'
    }))
    
    class Meta:
        model = TodoItem
        fields = ['title', 'description', 'due_date', 'priority', 'category', 
                 'tags', 'estimated_hours', 'attachment']
        widgets = {
            'due_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter task title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter task description'
            }),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'estimated_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Estimated hours',
                'step': '0.5',
                'min': '0'
            }),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date < timezone.now():
            raise forms.ValidationError("Due date cannot be in the past.")
        return due_date
    
    def clean_tags(self):
        tags = self.cleaned_data.get('tags', '')
        if tags:
            # Validate tag format
            tag_list = [tag.strip() for tag in tags.split(',')]
            for tag in tag_list:
                if not re.match(r'^[a-zA-Z0-9\s-]+$', tag):
                    raise forms.ValidationError(f"Invalid tag format: '{tag}'. Use only letters, numbers, spaces, and hyphens.")
        return tags

class TaskShareForm(forms.ModelForm):
    email = forms.EmailField(label="Share with (Email)", widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter user email'
    }))
    
    class Meta:
        model = TaskShare
        fields = ['permission']
        widgets = {
            'permission': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise forms.ValidationError("No user found with this email address.")
        return email

class TaskCommentForm(forms.ModelForm):
    class Meta:
        model = TaskComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Write a comment...'
            })
        }

class TaskFilterForm(forms.Form):
    STATUS_CHOICES = [
        ('', 'All Tasks'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
    ]
    
    PRIORITY_CHOICES = [('', 'All')] + TodoItem.PRIORITY_CHOICES
    CATEGORY_CHOICES = [('', 'All')] + TodoItem.CATEGORY_CHOICES
    
    search = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Search tasks...'
    }))
    status = forms.ChoiceField(required=False, choices=STATUS_CHOICES, widget=forms.Select(attrs={
        'class': 'form-control'
    }))
    priority = forms.ChoiceField(required=False, choices=PRIORITY_CHOICES, widget=forms.Select(attrs={
        'class': 'form-control'
    }))
    category = forms.ChoiceField(required=False, choices=CATEGORY_CHOICES, widget=forms.Select(attrs={
        'class': 'form-control'
    }))
    tag = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Filter by tag'
    }))