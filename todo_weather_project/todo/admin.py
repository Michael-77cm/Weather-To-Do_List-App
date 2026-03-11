from django.contrib import admin
from .models import TodoItem

@admin.register(TodoItem)
class TodoItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'priority', 'category', 'completed', 'created_date', 'due_date')
    list_filter = ('completed', 'priority', 'category', 'created_date')
    search_fields = ('title', 'description')
    date_hierarchy = 'created_date'
    ordering = ('-created_date',)
    list_editable = ('completed', 'priority')
    
    fieldsets = (
        ('Task Information', {
            'fields': ('title', 'description', 'user')
        }),
        ('Status', {
            'fields': ('completed', 'priority', 'category')
        }),
        ('Dates', {
            'fields': ('due_date',)
        }),
    )