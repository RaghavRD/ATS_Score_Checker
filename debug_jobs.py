import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rank_my_cv.settings')
django.setup()

from apps.jobs.services import JobSearchService

def test_service():
    service = JobSearchService()
    
    # Test 1: Standard Search
    print("Test 1: 'Python' in 'United States'")
    jobs = service.search_jobs(query="Python", location="United States")
    print(f"Found {len(jobs)} jobs")
    
    # Test 2: 'Remote' as location filter (Suspected Failure)
    print("\nTest 2: 'Python' with location='Remote'")
    jobs_remote_str = service.search_jobs(query="Python", location="Remote")
    print(f"Found {len(jobs_remote_str)} jobs")
    
    # Test 3: Correct Remote param
    print("\nTest 3: 'Python' with remote=true")
    jobs_remote_bool = service.search_jobs(query="Python", location="", remote="true")
    print(f"Found {len(jobs_remote_bool)} jobs")

if __name__ == "__main__":
    test_service()
