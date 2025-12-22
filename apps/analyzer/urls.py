from django.urls import path
from .views import ResumeUploadView, AnalysisHistoryView

app_name = 'analyzer'

urlpatterns = [
    path('', ResumeUploadView.as_view(), name='home'),
    path('history/', AnalysisHistoryView.as_view(), name='history'),
]
