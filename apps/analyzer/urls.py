from django.urls import path
from .views import ResumeUploadView, AnalysisHistoryView, TailorResumeView, InterviewPrepView

app_name = 'analyzer'

urlpatterns = [
    path('', ResumeUploadView.as_view(), name='home'),
    path('history/', AnalysisHistoryView.as_view(), name='history'),
    path('tailor/', TailorResumeView.as_view(), name='tailor_resume'),
    path('interview/', InterviewPrepView.as_view(), name='interview_prep'),
]
