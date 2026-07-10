from django.urls import path

from .views import video_progress

urlpatterns = [
    path("video-progress/", video_progress, name="api_video_progress"),
]
