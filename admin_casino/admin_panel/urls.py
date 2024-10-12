from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login_view'),
    path('users/', views.user_list, name='user_list'),
    path('create-test-user/', views.create_test_user, name='create_test_user'),
    path('projects/', views.project_list, name='project_list'),
    path('create-project/', views.create_project, name='create_project'),
    path('projects/<int:project_id>/', views.project_detail, name='project_detail'), 
    path('projects/<int:project_id>/delete/', views.delete_project, name='delete_project'),
    path('telegram_app/<int:hall_id>/', views.telegram_app_view, name='telegram_app_view'),
    path('process/', views.process_user_id, name='process_user_id'),
    path('start_bot/<int:project_id>/', views.start_bot_view, name='start_bot'),
    path('restart_bot/<int:project_id>/', views.restart_bot_view, name='restart_bot'),
    path('stop_bot/<int:project_id>/', views.stop_bot_view, name='stop_bot'),
    path('update_bot_settings/<int:project_id>/', views.update_bot_settings, name='update_bot_settings'),
    path('settings/', views.settings_view, name='settings'),
    path('update_settings/', views.update_settings, name='update_settings'),
]