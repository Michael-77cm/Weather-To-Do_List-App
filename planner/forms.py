from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Task, TaskAttachment, TaskRecurrence, TaskShare


class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254)
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email


class TaskForm(forms.ModelForm):

    create_series = forms.BooleanField(required=False, initial=True)
    apply_scope = forms.ChoiceField(
        required=False,
        choices=(('single', 'Only this task'), ('series', 'Entire series')),
        initial='single',
    )

    class Meta:
        model = Task
        fields = (
            'title',
            'description',
            'category',
            'status',
            'scheduled_for',
            'due_time',
            'recurrence',
            'recurrence_ends_on',
            'reminder_enabled',
        )
        widgets = {
            'scheduled_for': forms.DateInput(attrs={'type': 'date'}),
            'due_time': forms.TimeInput(attrs={'type': 'time'}),
            'recurrence_ends_on': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned = super().clean()
        recurrence = cleaned.get('recurrence')
        scheduled_for = cleaned.get('scheduled_for')
        recurrence_ends_on = cleaned.get('recurrence_ends_on')

        if recurrence and recurrence != TaskRecurrence.NONE and recurrence_ends_on and scheduled_for:
            if recurrence_ends_on < scheduled_for:
                self.add_error('recurrence_ends_on', 'Recurrence end date must be on or after task date.')
        if recurrence == TaskRecurrence.NONE:
            cleaned['recurrence_ends_on'] = None
        return cleaned


class TaskShareForm(forms.ModelForm):
    class Meta:
        model = TaskShare
        fields = ('recipient_email', 'can_edit', 'message')
        widgets = {
            'recipient_email': forms.EmailInput(attrs={'placeholder': 'friend@example.com'}),
            'message': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Optional message'}),
        }


class TaskAttachmentForm(forms.ModelForm):
    class Meta:
        model = TaskAttachment
        fields = ('file', 'name')