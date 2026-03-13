from django.urls import path
from . import views

app_name = 'todo'

urlpatterns = [
    path('', views.task_list, name='task_list'),
    path('task/new/', views.task_create, name='task_create'),
    path('task/<int:pk>/', views.task_detail, name='task_detail'),
    path('task/<int:pk>/update/', views.task_update, name='task_update'),
    path('task/<int:pk>/delete/', views.task_delete, name='task_delete'),
    path('task/<int:pk>/toggle/', views.task_mark_completed, name='task_mark_completed'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('calendar/tasks/', views.get_calendar_tasks, name='get_calendar_tasks'),
]