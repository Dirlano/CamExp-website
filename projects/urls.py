from django.urls import path
from .views import (
    dashboard, 
    schedule, 
    project_detail, 
    create_project, 
    update_project_status,
    expert_projects,
    completed_projects
)

app_name = 'projects'

urlpatterns = [
    path('dashboard/', dashboard, name='dashboard'),
    path('expert/projects/', expert_projects, name='expert_projects'),
    path('expert/completed/', completed_projects, name='completed_projects'),
    path('schedule/<int:project_id>/', schedule, name='schedule'),
    path('detail/<int:project_id>/', project_detail, name='project_detail'),
    path('create/<int:request_id>/', create_project, name='create_project'),
    path('update-status/<int:project_id>/', update_project_status, name='update_status'),
]