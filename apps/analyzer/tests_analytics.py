from django.test import TestCase
from django.contrib.auth.models import User
from apps.analyzer.models import AnalysisResult
from apps.analyzer.services.analytics import AnalysisStatsService
from datetime import datetime, timedelta

class AnalyticsServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="chartuser", password="password")
        
        # Create 3 scans with specific dates and scores
        # Scan 1: 3 days ago, Score 60
        s1 = AnalysisResult.objects.create(
            user=self.user,
            resume_filename="resume_v1.pdf",
            job_description_snippet="JD 1",
            final_score=60.0,
            keyword_score=50.0,
            semantic_score=60.0,
            formatting_score=80.0
        )
        s1.created_at = datetime.now() - timedelta(days=3)
        s1.save()

        # Scan 2: 2 days ago, Score 70
        s2 = AnalysisResult.objects.create(
            user=self.user,
            resume_filename="resume_v2.pdf",
            job_description_snippet="JD 1",
            final_score=70.0,
            keyword_score=70.0,
            semantic_score=70.0,
            formatting_score=70.0
        )
        s2.created_at = datetime.now() - timedelta(days=2)
        s2.save()

        # Scan 3: Today, Score 90
        AnalysisResult.objects.create(
            user=self.user,
            resume_filename="resume_final.pdf",
            job_description_snippet="JD 1",
            final_score=90.0,
            keyword_score=90.0,
            semantic_score=90.0,
            formatting_score=90.0
        )

    def test_stats_aggregation(self):
        stats = AnalysisStatsService.get_user_stats(self.user)
        
        # Verify Averages
        self.assertEqual(stats['total_scans'], 3)
        # Avg: (60+70+90)/3 = 73.33 -> 73.3
        self.assertEqual(stats['average_score'], 73.3)
        
        # Verify History List
        history = stats['history']
        self.assertEqual(len(history), 3)
        
        # Ensure sorting by date asc
        self.assertEqual(history[0]['score'], 60.0)
        self.assertEqual(history[1]['score'], 70.0)
        self.assertEqual(history[2]['score'], 90.0)
        
        print("\n\n--- Dashboard Stats Result ---")
        print(stats)
