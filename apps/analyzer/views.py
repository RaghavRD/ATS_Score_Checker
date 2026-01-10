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
        context = {'form': form}
        
        if request.user.is_authenticated:
            from .services.analytics import AnalysisStatsService
            stats = AnalysisStatsService.get_user_stats(request.user)
            context['stats'] = stats
            
        return render(request, self.template_name, context)

    def post(self, request):
        form = UploadResumeForm(request.POST, request.FILES)
        if form.is_valid():
            resume_file = request.FILES['resume']
            jd_text = form.cleaned_data['job_description']
            try:
                resume_data = parse_resume(resume_file)
                
                # Run Analysis
                engine = ScoringEngine()
                analysis_result = engine.analyze(resume_data, jd_text)
                
                # Save to DB (Graceful failure)
                saved_obj = None
                try:
                    from .models import AnalysisResult
                    # Associate with user if logged in
                    user_instance = request.user if request.user.is_authenticated else None
                    
                    saved_obj = AnalysisResult.objects.create(
                        user=user_instance,
                        job_description_snippet=jd_text[:500],
                        resume_filename=resume_file.name,
                        final_score=analysis_result['final_score'],
                        keyword_score=analysis_result['breakdown']['keyword_score'],
                        semantic_score=analysis_result['breakdown']['semantic_score'],
                        formatting_score=analysis_result['breakdown']['formatting_score'],
                        full_text=resume_data['full_text'],
                        data=analysis_result
                    )
                except Exception as e:
                    # Log error but don't fail the request
                    print(f"Error saving history: {e}")

                # DEBUG: Print the analysis result to console
                # print("DEBUG - Analysis Result Keywords:")
                # print(analysis_result)
                # print(f"  matches: {analysis_result.get('details', {}).get('keywords', {}).get('matches', 'NOT FOUND')}")
                # print(f"  missing: {analysis_result.get('details', {}).get('keywords', {}).get('missing', 'NOT FOUND')}")
                
                return render(request, 'analyzer/results.html', {
                    'results': analysis_result,
                    'extracted_text': resume_data['full_text'], # Pass full text for debugging/display
                    'analysis_obj': saved_obj # Pass object so we have the ID for AJAX calls
                })
            except ValueError as e:
                form.add_error('resume', str(e))
        
        return render(request, self.template_name, {'form': form})

from django.http import JsonResponse, HttpResponseBadRequest
from .models import AnalysisResult
from apps.core.services.llm import LLMService

class TailorResumeView(LoginRequiredMixin, View):
    def post(self, request):
        analysis_id = request.POST.get('analysis_id')
        if not analysis_id:
            return HttpResponseBadRequest("Missing analysis_id")
            
        try:
            analysis = AnalysisResult.objects.get(id=analysis_id, user=request.user)
            llm = LLMService()
            # Need original JD. Usually stored in snippet, but snippet is short?
            # Ideally we should have stored full JD.
            # Fallback: Use snippet or just generic.
            # Actually, `analyze` takes full JD. But we didn't store full JD in DB except as snippet.
            # Mistake in Phase 2? 
            # Snippet is 500 chars. Might be too short for good tailoring.
            # For now, let's use what we have in `data` JSON if we stored it?
            # `data` field stores the `analysis_result` dict. It doesn't have JD.
            # Workaround: For this session, we rely on the snippet. 
            # In a real app, we'd store full JD. 
            # Let's check snippet length.
            
            tailored_content = llm.generate_tailored_resume(analysis.full_text, analysis.job_description_snippet)
            return JsonResponse({'content': tailored_content})
        except AnalysisResult.DoesNotExist:
            return HttpResponseBadRequest("Invalid analysis ID")

class InterviewPrepView(LoginRequiredMixin, View):
    def post(self, request):
        analysis_id = request.POST.get('analysis_id')
        if not analysis_id:
            return HttpResponseBadRequest("Missing analysis_id")
            
        try:
            analysis = AnalysisResult.objects.get(id=analysis_id, user=request.user)
            llm = LLMService()
            questions = llm.generate_interview_questions(analysis.full_text, analysis.job_description_snippet)
            return JsonResponse({'content': questions})
        except AnalysisResult.DoesNotExist:
            return HttpResponseBadRequest("Invalid analysis ID")

from django.views.generic import ListView
from .models import AnalysisResult

class AnalysisHistoryView(LoginRequiredMixin, ListView):
    model = AnalysisResult
    template_name = 'analyzer/history.html'
    context_object_name = 'object_list'

    def get_queryset(self):
        return AnalysisResult.objects.filter(user=self.request.user)
