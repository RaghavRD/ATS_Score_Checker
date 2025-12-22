from abc import ABC, abstractmethod
from typing import Dict, Any, List
from .text_process import TextProcessor
from sentence_transformers import SentenceTransformer, util
import numpy as np

# Lazy load model to speed up dev restart, or load in AppConfig in production
_EMBEDDING_MODEL = None

def get_embedding_model():
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        # standard lightweight model
        _EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2') 
    return _EMBEDDING_MODEL

class BaseScorer(ABC):
    @abstractmethod
    def score(self, resume_data: Dict[str, Any], jd_text: str) -> Dict[str, Any]:
        pass

class KeywordScorer(BaseScorer):
    def __init__(self):
        self.processor = TextProcessor()

    def score(self, resume_data: Dict[str, Any], jd_text: str) -> Dict[str, Any]:
        full_text = resume_data.get('full_text', '')
        sections = resume_data.get('sections', {})
        
        jd_keywords = self.processor.extract_keywords(jd_text)
        
        if not jd_keywords:
            return {"score": 0, "matches": [], "missing": []}

        # Extract keywords from different sources
        full_text_keywords = self.processor.extract_keywords(full_text)
        
        # Section-specific sets for weighting
        skills_keywords = self.processor.extract_keywords(sections.get('skills', ''))
        exp_keywords = self.processor.extract_keywords(sections.get('experience', ''))
        
        matches = set()
        base_score = 0.0
        bonus_score = 0.0
        
        for word in jd_keywords:
            if word in full_text_keywords:
                matches.add(word)
                base_score += 1.0
                
                # Weighting: Bonus if found in relevant sections
                if word in skills_keywords:
                    bonus_score += 0.5
                elif word in exp_keywords:
                    bonus_score += 0.3
        
        # Score Calculation
        # Base Coverage: up to 80 points
        coverage_ratio = base_score / len(jd_keywords)
        coverage_points = coverage_ratio * 80
        
        # Bonus Points: up to 20 points
        # Max reasonable bonus is roughly 0.5 * len(keywords) (if all in skills)
        max_bonus = len(jd_keywords) * 0.5
        bonus_ratio = 0 if max_bonus == 0 else (bonus_score / max_bonus)
        bonus_points = bonus_ratio * 20
        
        final_score = min(100, round(coverage_points + bonus_points, 1))
        
        missing = jd_keywords - matches

        return {
            "score": final_score,
            "match_count": len(matches),
            "total_keywords": len(jd_keywords),
            "matches": list(matches),
            "missing": list(missing)
        }

class SemanticScorer(BaseScorer):
    def score(self, resume_data: Dict[str, Any], jd_text: str) -> Dict[str, Any]:
        # Semantic score uses full text for broad context
        resume_text = resume_data.get('full_text', '')
        
        model = get_embedding_model()
        
        # Compute embeddings
        processor = TextProcessor()
        clean_resume = processor.clean_text(resume_text)
        clean_jd = processor.clean_text(jd_text)

        emb1 = model.encode(clean_resume, convert_to_tensor=True)
        emb2 = model.encode(clean_jd, convert_to_tensor=True)

        cosine_score = util.cos_sim(emb1, emb2).item()
        
        # Normalize -1 to 1 into 0 to 100
        final_score = max(0.0, min(1.0, cosine_score)) * 100
        
        return {
            "score": round(final_score, 1)
        }

class FormattingScorer(BaseScorer):
    def score(self, resume_data: Dict[str, Any], jd_text: str) -> Dict[str, Any]:
        """
        Now uses structured section data to verify presence.
        """
        full_text = resume_data.get('full_text', '')
        sections = resume_data.get('sections', {})
        
        issues = []
        score = 100
        
        # Length check
        word_count = len(full_text.split())
        if word_count < 200:
            score -= 20
            issues.append("Resume might be too short (<200 words).")
        elif word_count > 1500:
            score -= 10
            issues.append("Resume might be too long (>1500 words).")

        # Section check (Smart Mode)
        required_sections = ['experience', 'education', 'skills']
        missing_sections = []
        
        for sec in required_sections:
            content = sections.get(sec, '').strip()
            # If empty or extremely short (parsing error or empty section)
            if not content or len(content) < 10:
                score -= 15
                missing_sections.append(sec.title())
        
        if missing_sections:
            issues.append(f"Missing or empty standard sections: {', '.join(missing_sections)}")

        return {
            "score": max(0, score),
            "issues": issues
        }

from apps.core.services.llm import LLMService

class ScoringEngine:
    def __init__(self):
        self.keyword_scorer = KeywordScorer()
        self.semantic_scorer = SemanticScorer()
        self.formatting_scorer = FormattingScorer()
        self.llm_service = LLMService()

    def analyze(self, resume_data: Dict[str, Any], jd_text: str) -> Dict[str, Any]:
        # resume_data contains 'full_text' and 'sections'
        
        k_res = self.keyword_scorer.score(resume_data, jd_text)
        s_res = self.semantic_scorer.score(resume_data, jd_text)
        f_res = self.formatting_scorer.score(resume_data, jd_text)
        
        # LLM Analysis (uses full text)
        ai_res = self.llm_service.get_analysis(resume_data['full_text'], jd_text)

        # Weighted Hybrid Score
        hybrid_score = (
            (k_res['score'] * 0.4) + 
            (s_res['score'] * 0.4) + 
            (f_res['score'] * 0.2)
        )

        return {
            "final_score": round(hybrid_score, 1),
            "breakdown": {
                "keyword_score": k_res['score'],
                "semantic_score": s_res['score'],
                "formatting_score": f_res['score']
            },
            "details": {
                "keywords": k_res,
                "formatting": f_res
            },
            "ai_analysis": ai_res
        }

