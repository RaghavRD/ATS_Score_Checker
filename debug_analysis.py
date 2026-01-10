import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rank_my_cv.settings')
django.setup()

from apps.analyzer.services.scorer import ScoringEngine

def test_scorer():
    print("--- Starting Scorer Debug ---")
    
    # Mock Data
    resume_data = {
        'full_text': """
        Raghav Desai
        Software Engineer
        
        EXPERIENCE
        Senior Developer at Tech Corp
        - Used Python and Django to build web apps.
        - Implemented REST APIs.
        
        SKILLS
        Python, Django, JavaScript, AWS
        """,
        'sections': {
            'experience': 'Senior Developer at Tech Corp\n- Used Python and Django to build web apps.',
            'skills': 'Python, Django, JavaScript, AWS'
        }
    }
    
    jd_text = """
    We are looking for a Python Developer.
    Must have experience with Django and REST APIs.
    Knowledge of AWS is a plus.
    """
    
    engine = ScoringEngine()
    try:
        results = engine.analyze(resume_data, jd_text)
        
        print("\n--- Analysis Result Keys ---")
        print(results.keys())
        
        print("\n--- Details Section ---")
        print(results.get('details', 'MISSING'))
        
        if 'details' in results:
            print("\n--- Keywords Detail ---")
            print(results['details'].get('keywords', 'MISSING_KEYWORDS'))
            
        print("\n--- Final Score ---")
        print(results.get('final_score'))
        
        print("\n--- AI Analysis ---")
        print(results.get('ai_analysis'))
        
    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_scorer()
