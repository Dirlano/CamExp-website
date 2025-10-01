from django.urls import path
from . import views

app_name = 'video_calls_api'

urlpatterns = [
    path('', views.CreateVideoCallView.as_view(), name='create_video_call'),
    path('<int:pk>/', views.VideoCallDetailView.as_view(), name='video_call_detail'),
    path('<int:pk>/end/', views.EndVideoCallView.as_view(), name='end_video_call'),
]