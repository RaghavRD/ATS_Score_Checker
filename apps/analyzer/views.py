from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import UploadResumeForm
from .services.parser import parse_resume

from .services.scorer import ScoringEngine

class ResumeUploadView(LoginRequiredMixin, View):
    template_name = 'analyzer/home.html'

    def get(self, request):
        form = UploadResumeForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = UploadResumeForm(request.POST, request.FILES)
        if form.is_valid():
            resume_file = request.FILES['resume']
            jd_text = form.cleaned_data['job_description']
            try:
                extracted_text = parse_resume(resume_file)
                
                # Run Analysis
                engine = ScoringEngine()
                analysis_result = engine.analyze(extracted_text, jd_text)
                
                # Save to DB (Graceful failure)
                try:
                    from .models import AnalysisResult
                    # Associate with user if logged in
                    user_instance = request.user if request.user.is_authenticated else None
                    
                    AnalysisResult.objects.create(
                        user=user_instance,
                        job_description_snippet=jd_text[:500],
                        resume_filename=resume_file.name,
                        final_score=analysis_result['final_score'],
                        keyword_score=analysis_result['breakdown']['keyword_score'],
                        semantic_score=analysis_result['breakdown']['semantic_score'],
                        formatting_score=analysis_result['breakdown']['formatting_score'],
                        data=analysis_result
                    )
                except Exception as e:
                    # Log error but don't fail the request
                    print(f"Error saving history: {e}")

                return render(request, 'analyzer/results.html', {
                    'results': analysis_result,
                    'extracted_text': extracted_text, # Optional: keep for debugging/transparency
                })
            except ValueError as e:
                form.add_error('resume', str(e))
        
        return render(request, self.template_name, {'form': form})

from django.views.generic import ListView
from .models import AnalysisResult

class AnalysisHistoryView(LoginRequiredMixin, ListView):
    model = AnalysisResult
    template_name = 'analyzer/history.html'
    context_object_name = 'object_list'

    def get_queryset(self):
        return AnalysisResult.objects.filter(user=self.request.user)
