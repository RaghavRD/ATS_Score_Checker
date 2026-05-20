from django.test import TestCase
from unittest.mock import patch, MagicMock
from apps.analyzer.models import AnalysisResult
from django.contrib.auth.models import User
from apps.jobs.services import JobSearchService
import json

class JobSearchServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.analysis = AnalysisResult.objects.create(
            user=self.user,
            final_score=85.0,
            keyword_score=80.0,
            semantic_score=90.0,
            formatting_score=85.0,
            full_text="Experienced Python Developer with 5 years in Django and AWS.",
            data={
                "sections": {
                    "skills": "Python\nDjango\nAWS\nDocker\nPostgreSQL",
                    "experience": "Senior Python Developer at Tech Corp",
                }
            }
        )
        self.service = JobSearchService()

    def test_get_inferred_filters(self):
        filters = self.service.get_inferred_filters(self.analysis.id)
        self.assertEqual(filters['title'], 'Python Developer')
        self.assertEqual(filters['location'], 'Remote')
        self.assertIn('Python', filters['keywords'])
        self.assertEqual(len(filters['keywords']), 5)

    @patch('urllib.request.urlopen')
    def test_search_jobs(self, mock_urlopen):
        # Mock API Response
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.read.return_value = json.dumps([
            {"id": "1", "title": "Python Dev", "location": "Remote", "url": "http://example.com"}
        ]).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        jobs = self.service.search_jobs(query="Python")
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]['title'], 'Python Dev')

    def test_calculate_match_scores(self):
        jobs = [
            {"title": "Java Developer", "description_text": "Need Java and Spring"},
            {"title": "Python Developer", "description_text": "Need Python and Django"}
        ]
        
        # We can use real scorers as they are deterministic and local
        scored_jobs = self.service.calculate_match_scores(jobs, self.analysis.id)
        
        # Python job should score higher than Java job
        python_job = next(j for j in scored_jobs if j['title'] == "Python Developer")
        java_job = next(j for j in scored_jobs if j['title'] == "Java Developer")
        
        self.assertGreater(python_job.get('match_score', 0), java_job.get('match_score', 0))
