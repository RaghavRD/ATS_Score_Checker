from django.urls import path
from .views import JobBoardView, JobSearchAPI

app_name = 'jobs'

urlpatterns = [
    path('', JobBoardView.as_view(), name='board'),
    path('api/search/', JobSearchAPI.as_view(), name='search_api'),
]
