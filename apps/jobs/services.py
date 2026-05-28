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

    @property
    def HEADERS(self):
        return {
            "x-rapidapi-host": "linkedin-job-search-api.p.rapidapi.com",
            "x-rapidapi-key": settings.RAPIDAPI_KEY,
        }

    def __init__(self):
        self.keyword_scorer = KeywordScorer()
        self.semantic_scorer = SemanticScorer()

    # Common job title patterns to look for in JD text
    _TITLE_PATTERNS = [
        r'(?:we are looking for|hiring|seeking|role\s*[:\-]?)\s+(?:a|an)?\s*([A-Z][A-Za-z\s\/\-]+?)(?:\s+to|\s+who|\s*\n|\s*\.)',
        r'^([A-Z][A-Za-z\s\/\-]{3,50})\s*\n',   # First capitalised line of JD
        r'(?:position|job title|role)\s*[:\-]\s*([A-Za-z\s\/\-]+)',
    ]

    # Skill → title mapping (expanded)
    _SKILL_TITLE_MAP = [
        (['react', 'vue', 'angular', 'frontend', 'front-end'], 'Frontend Developer'),
        (['node', 'express', 'backend', 'back-end', 'django', 'flask', 'fastapi'], 'Backend Developer'),
        (['python'], 'Python Developer'),
        (['java', 'spring'], 'Java Developer'),
        (['data science', 'machine learning', 'ml', 'pandas', 'scikit'], 'Data Scientist'),
        (['data analyst', 'tableau', 'power bi', 'sql', 'analytics'], 'Data Analyst'),
        (['devops', 'kubernetes', 'docker', 'ci/cd', 'terraform', 'aws', 'cloud'], 'DevOps Engineer'),
        (['ios', 'swift', 'android', 'kotlin', 'flutter', 'mobile'], 'Mobile Developer'),
        (['product manager', 'product management', 'roadmap'], 'Product Manager'),
        (['ux', 'ui design', 'figma', 'designer'], 'UX/UI Designer'),
        (['fullstack', 'full stack', 'full-stack'], 'Full Stack Developer'),
    ]

    def get_inferred_filters(self, analysis_id: int, optimized: bool = False) -> dict:
        """
        Extracts search filters from a saved analysis result.
        Tries to pull the job title from the resume text first, falls back to the
        job description patterns, and then falls back to skill-based inference.
        """
        import re
        try:
            analysis = AnalysisResult.objects.get(id=analysis_id)
            data = analysis.data
            sections = data.get('sections', {})
            jd_text = analysis.job_description_full or analysis.job_description_snippet

            # ── 1. Title: try extracting from resume text (first 5 lines or first experience line) ──
            title_suggestion = ''
            resume_lines = [l.strip() for l in analysis.full_text.splitlines() if l.strip()]
            
            # Look at lines 2 to 5 (avoiding the candidate's name on line 1)
            potential_titles = []
            for line in resume_lines[1:5]:
                if len(line.split()) < 5 and not re.search(r'\d|@|\+|http|:|www', line):
                    potential_titles.append(line)
            
            if potential_titles:
                title_suggestion = potential_titles[0]
            
            # Try parsing from experience section header if not found in top lines
            if not title_suggestion:
                exp_text = sections.get('experience', '')
                first_exp_line = next((l.strip() for l in exp_text.splitlines() if l.strip()), '')
                if first_exp_line:
                    parts = re.split(r'[|\-,]|\bat\b', first_exp_line, flags=re.IGNORECASE)
                    candidate = parts[0].strip()
                    if len(candidate.split()) < 5 and not re.search(r'\d|@', candidate):
                        title_suggestion = candidate

            # Fallback: Extract from Job Description text patterns
            if not title_suggestion:
                for pattern in self._TITLE_PATTERNS:
                    m = re.search(pattern, jd_text, re.IGNORECASE | re.MULTILINE)
                    if m:
                        candidate = m.group(1).strip().rstrip('.,;')
                        if 3 < len(candidate) < 60 and not re.search(r'\d', candidate):
                            title_suggestion = candidate
                            break

            # Fallback: Skill-based heuristic
            if not title_suggestion:
                skills_text = (sections.get('skills', '') + ' ' + jd_text).lower()
                for skill_keys, title in self._SKILL_TITLE_MAP:
                    if any(k in skills_text for k in skill_keys):
                        title_suggestion = title
                        break

            # ── 2. Top skills for keywords field (multi-delimiter split) ──────────────────
            skills_raw = sections.get('skills', '')
            skills_list = re.split(r'[,;\n•|·\t]', skills_raw)
            top_skills = [s.strip() for s in skills_list if s.strip()]

            unique_skills = []
            for s in top_skills:
                if s.lower() not in [u.lower() for u in unique_skills] and len(s) > 1 and len(s) < 30:
                    unique_skills.append(s)

            # If optimized, append missing keywords from analysis details
            if optimized:
                missing_kws = data.get('details', {}).get('keywords', {}).get('missing', [])
                for kw in missing_kws:
                    if kw.lower() not in [u.lower() for u in unique_skills] and len(kw) > 1 and len(kw) < 30:
                        unique_skills.append(kw)

            selected_skills = unique_skills[:6]

            return {
                'title':      title_suggestion,
                'location':   'India',
                'keywords':   selected_skills,
                'skills_text': ', '.join(selected_skills),
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

    def calculate_match_scores(self, jobs: list, analysis_id: int, optimized: bool = False) -> list:
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
                k_res = self.keyword_scorer.score(resume_data, jd_text)
                s_res = self.semantic_scorer.score(resume_data, jd_text)
                
                k_score = k_res['score']
                match_count = k_res.get('match_count', 0)
                
                if optimized:
                    # Boost match score by simulating the insertion of missing keywords
                    missing_count = k_res.get('missing_count', 0)
                    resolved = round(missing_count * 0.8) # assume 80% keyword gap resolution
                    match_count += resolved
                    k_score = min(100.0, k_score + (resolved / max(1, k_res.get('total_keywords', 1)) * 100))
                    
                # Weighted Average (50/50 for now)
                final_score = (k_score * 0.5) + (s_res['score'] * 0.5)
                if optimized:
                    final_score = min(100.0, final_score + 10.0) # dynamic semantic boost
                    
                job['match_score'] = round(final_score, 1)
                job['keyword_matches'] = match_count
            
            # Sort by match score descending
            jobs.sort(key=lambda x: x.get('match_score', 0), reverse=True)
            return jobs
            
        except AnalysisResult.DoesNotExist:
            return jobs
