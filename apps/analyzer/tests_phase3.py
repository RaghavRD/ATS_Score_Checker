from django.test import TestCase, Client
from django.contrib.auth.models import User
from unittest.mock import patch
from django.urls import reverse
from apps.analyzer.models import AnalysisResult

class Phase3Tests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.client = Client()
        self.client.login(username="testuser", password="password")
        
        self.analysis = AnalysisResult.objects.create(
            user=self.user,
            resume_filename="test.pdf",
            job_description_snippet="Python Developer needed.",
            final_score=80.0,
            keyword_score=80.0,
            semantic_score=80.0,
            formatting_score=80.0,
            full_text="I am a Python Developer.",
            data={}
        )
        self.tailor_url = reverse('analyzer:tailor_resume')
        self.interview_url = reverse('analyzer:interview_prep')

    @patch('apps.core.services.llm.LLMService.generate_tailored_resume')
    def test_tailor_resume_view(self, mock_tailor):
        mock_tailor.return_value = "<h3>Mock Tailored Resume</h3>"
        
        response = self.client.post(self.tailor_url, {'analysis_id': self.analysis.id})
        
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'content': "<h3>Mock Tailored Resume</h3>"})
        mock_tailor.assert_called_once()
    
    @patch('apps.core.services.llm.LLMService.generate_interview_questions')
    def test_interview_prep_view(self, mock_interview):
        mock_interview.return_value = "<h3>Mock Questions</h3>"
        
        response = self.client.post(self.interview_url, {'analysis_id': self.analysis.id})
        
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'content': "<h3>Mock Questions</h3>"})
        mock_interview.assert_called_once()

    def test_missing_id_error(self):
        response = self.client.post(self.tailor_url, {})
        self.assertEqual(response.status_code, 400)
        
    def test_invalid_id_error(self):
        response = self.client.post(self.tailor_url, {'analysis_id': 9999})
        self.assertEqual(response.status_code, 400)
