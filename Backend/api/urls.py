from django.urls import path
from .views import StoryCreativityAPIView


urlpatterns = [
    path('story/', StoryCreativityAPIView.as_view(), name='story'),
]
