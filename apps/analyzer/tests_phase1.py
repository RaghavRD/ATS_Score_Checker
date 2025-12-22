from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.analyzer.services.text_process import SectionExtractor, TextProcessor
from apps.analyzer.services.scorer import KeywordScorer, FormattingScorer
import json

class Phase1VerificationTest(TestCase):
    def setUp(self):
        # Increased length to >200 words to pass Formatting check
        self.resume_text = """
        John Doe -- Software Engineer
        
        Professional Summary
        Experienced Python developer with a focus on AI. I have built multiple applications using Django and React.
        My expertise includes cloud architecture, specifically with AWS and Azure.
        I am looking for a challenging role where I can leverage my skills in Python and Machine Learning.
        
        Experience
        Software Engineer at Google (2020-Present)
        - Developed search ranking algorithms using Python and C++.
        - Optimized database queries for high traffic systems.
        - Collaborated with cross-functional teams to deliver features.
        - Used AWS Lambda and EC2 for deployment.
        - Implemented CI/CD pipelines using Jenkins.
        - Mentored junior developers and conducted code reviews.
        - (Adding filler text to reach word count limit for the formatting scorer which requires >200 words)
        - Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        - Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
        - Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
        - Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
        - More filler text to ensure we are definitely over the 200 word count limit.
        - Python is great. Django is great. AWS is great.
        
        Skills
        Python, Django, React, AWS, Docker, Kubernetes, PostgreSQL, Redis, Linux, Git.
        Machine Learning, AI, Scikit-Learn, Pandas, NumPy.
        
        Education
        BS Computer Science -- University of Tech
        Graduated with Honors. 
        Coursework: Data Structures, Algorithms, OS, Databases.
        """
        
        self.clean_resume_text = self.resume_text.strip()
        
        self.jd_text = "Looking for a Python Developer with Django and AWS experience."

    def test_section_extractor(self):
        extractor = SectionExtractor()
        sections = extractor.extract_sections(self.clean_resume_text)
        
        # print(json.dumps(sections, indent=2))
        
        self.assertIn("Python, Django, React, AWS", sections['skills'])
        self.assertIn("Software Engineer at Google", sections['experience'])
        self.assertIn("BS Computer Science", sections['education'])

    def test_weighted_scoring(self):
        # mock structured data
        extractor = SectionExtractor()
        sections = extractor.extract_sections(self.clean_resume_text)
        resume_data = {
            "full_text": self.clean_resume_text,
            "sections": sections
        }
        
        scorer = KeywordScorer()
        result = scorer.score(resume_data, self.jd_text)
        
        # We expect high score.
        # Keywords in JD: Python, Developer, Django, AWS, Experience.
        match_count = result['match_count']
        self.assertGreaterEqual(match_count, 3) # At least Python, Django, AWS
        self.assertTrue(result['score'] > 80, f"Score {result['score']} should be high due to bonuses")

    def test_formatting_scorer(self):
        extractor = SectionExtractor()
        sections = extractor.extract_sections(self.clean_resume_text)
        resume_data = {
            "full_text": self.clean_resume_text,
            "sections": sections
        }
        
        scorer = FormattingScorer()
        result = scorer.score(resume_data, self.jd_text)
        
        print("\n\n--- Formatting Score Result ---")
        print(json.dumps(result, indent=2))
        
        self.assertEqual(result['score'], 100, "Should be perfect score as all sections are present")
