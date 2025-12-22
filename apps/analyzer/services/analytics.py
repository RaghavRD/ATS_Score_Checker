from django.db.models import Avg, Count
from ..models import AnalysisResult

class AnalysisStatsService:
    @staticmethod
    def get_user_stats(user):
        """
        Aggregates stats for the dashboard.
        Returns: {
            'history': [{'date': '...', 'score': 85}, ...],
            'average_score': 75,
            'total_scans': 10
        }
        """
        queryset = AnalysisResult.objects.filter(user=user).order_by('created_at')
        
        total_scans = queryset.count()
        if total_scans == 0:
            return None
            
        params = queryset.aggregate(
            avg_score=Avg('final_score'),
            avg_keyword=Avg('keyword_score'),
            avg_semantic=Avg('semantic_score')
        )
        
        history_data = [
            {
                'date': obj.created_at.strftime("%Y-%m-%d"),
                'score': obj.final_score
            }
            for obj in queryset
        ]
        
        return {
            'total_scans': total_scans,
            'average_score': round(params['avg_score'] or 0, 1),
            'averages': {
                'keyword': round(params['avg_keyword'] or 0, 1),
                'semantic': round(params['avg_semantic'] or 0, 1)
            },
            'history': history_data
        }
