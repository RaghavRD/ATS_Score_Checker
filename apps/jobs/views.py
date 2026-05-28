from django.shortcuts import render
from django.views.generic import TemplateView, View
from django.http import JsonResponse
from .services import JobSearchService

class JobBoardView(TemplateView):
    template_name = "jobs/board.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        analysis_id = self.request.GET.get('analysis_id') or self.kwargs.get('analysis_id')
        optimized = self.request.GET.get('optimized', 'false').lower() == 'true'
        
        service = JobSearchService()
        initial_filters = {}
        
        if analysis_id:
            initial_filters = service.get_inferred_filters(analysis_id, optimized=optimized)
            context['analysis_id'] = analysis_id
            context['optimized'] = optimized
        
        context['filters'] = initial_filters
        return context

class JobSearchAPI(View):
    def get(self, request, *args, **kwargs):
        service = JobSearchService()
        
        # Extract params
        query = request.GET.get('title_filter')
        location = request.GET.get('location_filter')
        optimized = request.GET.get('optimized', 'false').lower() == 'true'
        
        # Perform Search
        params = {k: v for k, v in request.GET.items() if k not in ['analysis_id', 'match_scores', 'optimized']}
        
        jobs = service.search_jobs(
            query=query, 
            location=location,
            **params
        )
        
        # Calculate Match Scores if analysis_id provided
        analysis_id = request.GET.get('analysis_id')
        if analysis_id and jobs:
            jobs = service.calculate_match_scores(jobs, analysis_id, optimized=optimized)
            
        return JsonResponse({'jobs': jobs}, safe=False)
