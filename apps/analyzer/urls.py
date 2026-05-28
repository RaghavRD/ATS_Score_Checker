from django.urls import path
from .views import (
    ResumeUploadView,
    AnalysisHistoryView,
    AnalysisDetailView,
    TailorResumeView,
    InterviewPrepView,
)
from .mock_urls import mock_results_view

app_name = 'analyzer'

urlpatterns = [
    path('', ResumeUploadView.as_view(), name='home'),
    path('history/', AnalysisHistoryView.as_view(), name='history'),
    path('history/<int:pk>/', AnalysisDetailView.as_view(), name='detail'),
    path('tailor/', TailorResumeView.as_view(), name='tailor_resume'),
    path('interview/', InterviewPrepView.as_view(), name='interview_prep'),
    path('mock-results/', mock_results_view, name='mock_results'),
]
