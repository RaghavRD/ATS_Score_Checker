from django.shortcuts import render
from django.views.generic import TemplateView, View
from django.http import JsonResponse
from .services import JobSearchService

class JobBoardView(TemplateView):
    template_name = "jobs/board.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        analysis_id = self.request.GET.get('analysis_id') or self.kwargs.get('analysis_id')
        
        service = JobSearchService()
        initial_filters = {}
        
        if analysis_id:
            initial_filters = service.get_inferred_filters(analysis_id)
            context['analysis_id'] = analysis_id
        
        context['filters'] = initial_filters
        return context

class JobSearchAPI(View):
    def get(self, request, *args, **kwargs):
        service = JobSearchService()
        
        # Extract params
        query = request.GET.get('title_filter')
        location = request.GET.get('location_filter')
        # ... other filters from request if needed
        
        # Perform Search
        # We pass request.GET to allow all supported params to flow through
        # cleaned of course by the service or just passed as kwargs
        params = {k: v for k, v in request.GET.items() if k not in ['analysis_id', 'match_scores']}
        
        jobs = service.search_jobs(
            query=query, 
            location=location,
            **params
        )
        
        # Calculate Match Scores if analysis_id provided
        analysis_id = request.GET.get('analysis_id')
        if analysis_id and jobs:
            jobs = service.calculate_match_scores(jobs, analysis_id)
            
        return JsonResponse({'jobs': jobs}, safe=False)
