from django.urls import path
from . import views

urlpatterns = [
    path('users/', views.user_list, name='user_list'),
    path('create-test-user/', views.create_test_user, name='create_test_user'),
    path('projects/', views.project_list, name='project_list'),
    path('create-project/', views.create_project, name='create_project'),
    path('projects/<int:project_id>/', views.project_detail, name='project_detail'), 
    path('projects/<int:project_id>/delete/', views.delete_project, name='delete_project'),
    path('telegram_app/', views.telegram_app_view, name='telegram_app'),
    path('process', views.process_user_id, name='process_user_id'),
    
]