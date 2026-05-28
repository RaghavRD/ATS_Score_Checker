from django.db.models import Avg, Max
from ..models import AnalysisResult


class AnalysisStatsService:
    @staticmethod
    def get_user_stats(user):
        """
        Returns aggregated stats for the logged-in user's dashboard.
        Includes per-dimension history for trend charts.
        """
        queryset = AnalysisResult.objects.filter(user=user).order_by('created_at')
        total_scans = queryset.count()

        if total_scans == 0:
            return None

        params = queryset.aggregate(
            avg_score=Avg('final_score'),
            avg_keyword=Avg('keyword_score'),
            avg_semantic=Avg('semantic_score'),
            avg_formatting=Avg('formatting_score'),
            best_score=Max('final_score'),
        )

        history_data = [
            {
                'date':       obj.created_at.strftime('%b %d'),
                'score':      round(obj.final_score, 1),
                'keyword':    round(obj.keyword_score, 1),
                'semantic':   round(obj.semantic_score, 1),
                'formatting': round(obj.formatting_score, 1),
                'filename':   obj.resume_filename,
            }
            for obj in queryset
        ]

        return {
            'total_scans':   total_scans,
            'average_score': round(params['avg_score'] or 0, 1),
            'best_score':    round(params['best_score'] or 0, 1),
            'averages': {
                'keyword':    round(params['avg_keyword'] or 0, 1),
                'semantic':   round(params['avg_semantic'] or 0, 1),
                'formatting': round(params['avg_formatting'] or 0, 1),
            },
            'history': history_data,
        }
