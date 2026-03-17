from django.urls import path

from . import views

app_name = 'planner'

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('tasks/create/', views.create_task, name='create_task'),
    path('tasks/<int:task_id>/update/', views.update_task, name='update_task'),
    path('tasks/<int:task_id>/delete/', views.delete_task, name='delete_task'),
    path('tasks/<int:task_id>/toggle/', views.toggle_task_status, name='toggle_task_status'),
    path('tasks/<int:task_id>/share/', views.share_task, name='share_task'),
    path('tasks/<int:task_id>/attachments/upload/', views.upload_attachment, name='upload_attachment'),
    path('attachments/<int:attachment_id>/delete/', views.delete_attachment, name='delete_attachment'),
    path('invites/<str:token>/', views.invite_detail, name='invite_detail'),
    path('invites/<int:share_id>/accept/', views.accept_invite, name='accept_invite'),
    path('invites/<int:share_id>/decline/', views.decline_invite, name='decline_invite'),
    path('invites/<int:share_id>/revoke/', views.revoke_invite, name='revoke_invite'),
    path('api/cities/', views.city_search, name='city_search'),
    path('api/weather/', views.weather_lookup, name='weather_lookup'),
]