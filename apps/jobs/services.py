import json
import logging
import urllib.request
import urllib.parse
import ssl
from django.conf import settings
from apps.analyzer.models import AnalysisResult
from apps.analyzer.services.scorer import KeywordScorer, SemanticScorer

logger = logging.getLogger(__name__)

class JobSearchService:
    BASE_URL = "https://linkedin-job-search-api.p.rapidapi.com/active-jb-24h"
    HEADERS = {
        "x-rapidapi-host": "linkedin-job-search-api.p.rapidapi.com",
        "x-rapidapi-key": "832bae4e1cmshba851e21a8e0a0cp1106cejsnb8fdebe31e7d"  
    }

    def __init__(self):
        self.keyword_scorer = KeywordScorer()
        self.semantic_scorer = SemanticScorer()

    def get_inferred_filters(self, analysis_id: int) -> dict:
        """
        Extracts filters (Title, Location, Skills) from an analysis result.
        Returns a dictionary of initial values for the search form.
        """
        try:
            analysis = AnalysisResult.objects.get(id=analysis_id)
            data = analysis.data
            sections = data.get('sections', {})
            
            # 1. Title (Inferred from Experience or Summary or simple heuristic)
            # This is hard to get perfectly without NLP, but we can look for the most recent role.
            # For now, let's default to a generic "Software Engineer" or try to parse the first line of experience?
            # A safer bet is to leave it empty or use a placeholder if we can't be sure.
            # However, the user wants personalization. 
            # Let's try to grab the first "Title-like" string from Experience if possible, or fall back to extracting noun phrases.
            # Simpler approach: Look at the uploaded filename? No.
            # Let's check if 'job_description_snippet' has a title? No, that's target JD.
            # We will return empty title to let user fill it, OR suggest based on skills (e.g. "Python Developer" if Python is top skill).
            
            skills_text = sections.get('skills', '')
            top_skills = [s.strip() for s in skills_text.splitlines() if s.strip()]
            
            # Simple heuristic: If "Python" in skills -> "Python Developer"
            title_suggestion = ""
            if "python" in skills_text.lower():
                title_suggestion = "Python Developer"
            elif "data" in skills_text.lower():
                title_suggestion = "Data Analyst"
            elif "react" in skills_text.lower():
                title_suggestion = "React Developer"
                
            # 2. Location
            # We don't have user location in model yet. Default to "Remote" or "United States"
            location_suggestion = "Remote"
            
            # 3. Keywords (Skills)
            # Take top 5 lines/items from skills
            keywords = top_skills[:5] if top_skills else []
            
            return {
                "title": title_suggestion,
                "location": location_suggestion,
                "keywords": keywords, # For display/editing
                "skills_text": ", ".join(keywords) # For API query if needed
            }
            
        except AnalysisResult.DoesNotExist:
            return {}

    def search_jobs(self, query: str = None, location: str = "United States", 
                   limit: int = 10, offset: int = 0, **kwargs) -> list:
        """
        Executes search against RapidAPI.
        """
        params = {
            "limit": str(limit),
            "offset": str(offset),
            "title_filter": query if query else "",
            "location_filter": location,
            "description_type": "text",
            **kwargs
        }
        
        # Handle "Remote" location input by converting to remote=true param
        if location and location.lower().strip() == 'remote':
            params['location_filter'] = ''  # Clear invalid location
            params['remote'] = 'true'
        
        # Clean empty params
        params = {k: v for k, v in params.items() if v}

        query_string = urllib.parse.urlencode(params)
        url = f"{self.BASE_URL}?{query_string}"
        
        try:
            req = urllib.request.Request(url, headers=self.HEADERS)
            # TODO: Add caching here (using Django cache) to avoid API costs
            
            # Unverified context for dev simplicity (be careful in prod)
            context = ssl._create_unverified_context()
            
            with urllib.request.urlopen(req, context=context) as response:
                if response.getcode() == 200:
                    data = response.read()
                    jobs = json.loads(data)
                    return jobs if isinstance(jobs, list) else []
                else:
                    logger.error(f"RapidAPI returned status: {response.getcode()}")
                    return []
                    
        except Exception as e:
            logger.error(f"Job search failed: {e}")
            return []

    def calculate_match_scores(self, jobs: list, analysis_id: int) -> list:
        """
        Calculates match score for each job against the analysis resume.
        Modifies the job dicts in-place (adds 'match_score').
        Returns the sorted list.
        """
        try:
            analysis = AnalysisResult.objects.get(id=analysis_id)
            resume_data = {
                'full_text': analysis.full_text,
                'sections': analysis.data.get('sections', {})
            }
            
            for job in jobs:
                jd_text = job.get('description_text', '') or job.get('title', '')
                
                # Fast scoring (No LLM)
                # 1. Keyword Score
                k_res = self.keyword_scorer.score(resume_data, jd_text)
                
                # 2. Semantic Score (Lightweight embedding)
                s_res = self.semantic_scorer.score(resume_data, jd_text)
                
                # Weighted Average (50/50 for now)
                final_score = (k_res['score'] * 0.5) + (s_res['score'] * 0.5)
                job['match_score'] = round(final_score, 1)
                job['keyword_matches'] = k_res.get('match_count', 0)
            
            # Sort by match score descending
            jobs.sort(key=lambda x: x.get('match_score', 0), reverse=True)
            return jobs
            
        except AnalysisResult.DoesNotExist:
            return jobs
