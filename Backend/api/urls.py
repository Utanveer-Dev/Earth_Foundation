from django.urls import path
from .views import StoryCreativityView


urlpatterns = [
    path('story/', StoryCreativityView.as_view(), name='story'),
]
