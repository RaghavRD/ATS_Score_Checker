from django.shortcuts import render
from django.urls import path

def mock_results_view(request):
    mock_results = {
        "final_score": 75.5,
        "breakdown": {
            "keyword_score": 80.0,
            "semantic_score": 70.0,
            "formatting_score": 90.0
        },
        "details": {
            "keywords": {
                "match_count": 5,
                "matches": ["Python", "Django", "AWS", "API", "REST"],
                "missing": ["Docker", "Kubernetes", "CI/CD"]
            },
            "formatting": {
                "issues": ["Resume is slightly short."]
            }
        },
        "ai_analysis": {
            "summary": "This is a MOCK SUMMARY. The candidate looks good but needs more cloud experience.",
            "experience_rating": "High",
            "strengths": ["Backend Dev", "API Design", "Cloud Basics"],
            "missing_skills": ["Containerization", "Orchestration"],
            "suggestions": ["Learn Docker", "Build a K8s cluster"]
        }
    }
    return render(request, 'analyzer/results.html', {
        'results': mock_results,
        'extracted_text': "Raghav Desai\nPython Developer...",
        'analysis_obj': None  # Mimic unsaved object
    })

urlpatterns = [
    path('mock_results/', mock_results_view),
]
