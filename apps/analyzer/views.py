from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseBadRequest

from .forms import UploadResumeForm
from .models import AnalysisResult
from .services.parser import parse_resume
from .services.scorer import ScoringEngine
from apps.core.services.llm import LLMService


class ResumeUploadView(View):
    """
    Open to everyone — anonymous users can analyze; logged-in users get
    their history stats and results are persisted to their account.
    """
    template_name = 'analyzer/home.html'

    def get(self, request):
        initial = {}
        # Re-scan: pre-fill JD from a saved analysis
        rescan_id = request.GET.get('rescan')
        if rescan_id and request.user.is_authenticated:
            try:
                prev = AnalysisResult.objects.get(pk=rescan_id, user=request.user)
                initial['job_description'] = prev.job_description_full or prev.job_description_snippet
            except AnalysisResult.DoesNotExist:
                pass

        form = UploadResumeForm(initial=initial)
        context = {'form': form, 'rescan': bool(initial)}

        if request.user.is_authenticated:
            from .services.analytics import AnalysisStatsService
            stats = AnalysisStatsService.get_user_stats(request.user)
            context['stats'] = stats

        return render(request, self.template_name, context)

    def post(self, request):
        form = UploadResumeForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        resume_file = request.FILES['resume']
        jd_text = form.cleaned_data['job_description']

        try:
            resume_data = parse_resume(resume_file)
        except ValueError as e:
            form.add_error('resume', str(e))
            return render(request, self.template_name, {'form': form})

        engine = ScoringEngine()
        analysis_result = engine.analyze(resume_data, jd_text)

        saved_obj = None
        try:
            user_instance = request.user if request.user.is_authenticated else None
            saved_obj = AnalysisResult.objects.create(
                user=user_instance,
                job_description_snippet=jd_text[:500],
                job_description_full=jd_text,          # full JD saved
                resume_filename=resume_file.name,
                final_score=analysis_result['final_score'],
                keyword_score=analysis_result['breakdown']['keyword_score'],
                semantic_score=analysis_result['breakdown']['semantic_score'],
                formatting_score=analysis_result['breakdown']['formatting_score'],
                full_text=resume_data['full_text'],
                data=analysis_result,
            )
        except Exception as e:
            print(f"Error saving analysis: {e}")

        return render(request, 'analyzer/results.html', {
            'results': analysis_result,
            'analysis_obj': saved_obj,
            'is_anonymous': not request.user.is_authenticated,
        })


class AnalysisDetailView(LoginRequiredMixin, DetailView):
    """
    Re-renders a saved analysis result from the DB — powers "View Details"
    in the history page.
    """
    model = AnalysisResult
    template_name = 'analyzer/results.html'

    def get_queryset(self):
        return AnalysisResult.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        obj = self.object
        ctx['results'] = obj.data
        ctx['analysis_obj'] = obj
        ctx['is_anonymous'] = False
        ctx['from_history'] = True
        return ctx


class TailorResumeView(LoginRequiredMixin, View):
    def post(self, request):
        analysis_id = request.POST.get('analysis_id')
        if not analysis_id:
            return HttpResponseBadRequest("Missing analysis_id")

        try:
            analysis = AnalysisResult.objects.get(id=analysis_id, user=request.user)
        except AnalysisResult.DoesNotExist:
            return HttpResponseBadRequest("Invalid analysis ID")

        # Use full JD now that we store it
        jd = analysis.job_description_full or analysis.job_description_snippet
        llm = LLMService()
        content = llm.generate_tailored_resume(analysis.full_text, jd)
        return JsonResponse({'content': content})


class InterviewPrepView(LoginRequiredMixin, View):
    def post(self, request):
        analysis_id = request.POST.get('analysis_id')
        if not analysis_id:
            return HttpResponseBadRequest("Missing analysis_id")

        try:
            analysis = AnalysisResult.objects.get(id=analysis_id, user=request.user)
        except AnalysisResult.DoesNotExist:
            return HttpResponseBadRequest("Invalid analysis ID")

        jd = analysis.job_description_full or analysis.job_description_snippet
        llm = LLMService()
        data = llm.generate_interview_questions(analysis.full_text, jd)
        return JsonResponse(data)


class AnalysisHistoryView(LoginRequiredMixin, ListView):
    model = AnalysisResult
    template_name = 'analyzer/history.html'
    context_object_name = 'object_list'

    def get_queryset(self):
        return AnalysisResult.objects.filter(user=self.request.user)
