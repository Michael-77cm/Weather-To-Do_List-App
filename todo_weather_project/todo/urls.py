from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    # Password reset
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='todo/registration/password_reset.html'
        ),
        name='password_reset',
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='todo/registration/password_reset_done.html'
        ),
        name='password_reset_done',
    ),
    path(
        'password-reset-confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='todo/registration/password_reset_confirm.html'
        ),
        name='password_reset_confirm',
    ),
    path(
        'password-reset-complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='todo/registration/password_reset_complete.html'
        ),
        name='password_reset_complete',
    ),

    # Todo
    path('', views.index, name='index'),
    path('add/', views.add_todo, name='add_todo'),
    path('edit/<int:todo_id>/', views.edit_todo, name='edit_todo'),
    path('delete/<int:todo_id>/', views.delete_todo, name='delete_todo'),
    path('toggle/<int:todo_id>/', views.toggle_complete, name='toggle_complete'),
    path('task/<int:todo_id>/', views.task_detail, name='task_detail'),

    # Sharing
    path('share/<int:todo_id>/', views.share_task, name='share_task'),
    path('manage-shares/<int:todo_id>/', views.manage_shares, name='manage_shares'),
    path('shared-with-me/', views.shared_with_me, name='shared_with_me'),
    path('accept-share/<uuid:token>/', views.accept_share, name='accept_share'),

    # Notifications
    path('notifications/', views.notifications, name='notifications'),
    path(
        'notifications/mark-read/<int:notification_id>/',
        views.mark_notification_read,
        name='mark_notification_read',
    ),

    # Weather
    path('weather/', views.weather_view, name='weather'),
]
