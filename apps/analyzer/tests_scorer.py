from django.test import TestCase
from .services.scorer import ScoringEngine, KeywordScorer, FormattingScorer

class ScorerTests(TestCase):
    def setUp(self):
        self.engine = ScoringEngine()

    def test_keyword_scorer_exact_match(self):
        scorer = KeywordScorer()
        resume = "I am a Python Developer with Django experience."
        jd = "We need a Python Developer with Django skills."
        
        # Extracted keywords should overlap: Python, Developer, Django
        score = scorer.score(resume, jd)
        # We expect a high score. 
        # Keywords in JD: need, Python, Developer, Django, skills (approx)
        # Matches: Python, Developer, Django
        self.assertGreater(score['score'], 50)
        self.assertIn('python', [x.lower() for x in score['matches']])

    def test_formatting_scorer_missing_sections(self):
        scorer = FormattingScorer()
        resume = "Just a short resume hello world."
        jd = "irrelevant"
        
        result = scorer.score(resume, jd)
        self.assertLess(result['score'], 100)
        self.assertTrue(any("too short" in issue for issue in result['issues']))
        self.assertTrue(any("Missing standard sections" in issue for issue in result['issues']))

    def test_full_engine_flow(self):
        resume = "Senior Python Developer. Experience: 5 years. Education: BSc CS."
        jd = "Looking for Python Developer."
        
        result = self.engine.analyze(resume, jd)
        self.assertIn('final_score', result)
        self.assertIn('breakdown', result)
        # Check weighted calculation
        # Formatting should be decent (has sections, maybe short?)
        # Keywords should match Python
        self.assertGreater(result['final_score'], 0)
