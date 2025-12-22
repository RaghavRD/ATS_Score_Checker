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
    def score(self, resume_text: str, jd_text: str) -> Dict[str, Any]:
        pass

class KeywordScorer(BaseScorer):
    def __init__(self):
        self.processor = TextProcessor()

    def score(self, resume_text: str, jd_text: str) -> Dict[str, Any]:
        resume_keywords = self.processor.extract_keywords(resume_text)
        jd_keywords = self.processor.extract_keywords(jd_text)
        
        if not jd_keywords:
            return {"score": 0, "matches": [], "missing": []}

        # Calculate overlap
        matches = resume_keywords.intersection(jd_keywords)
        missing = jd_keywords - matches
        
        # Jaccard index or simple coverage? 
        # Simple coverage (Recall) is usually better for ATS: "Do you have the required skills?"
        coverage = len(matches) / len(jd_keywords)
        score = round(coverage * 100, 1)

        return {
            "score": score,
            "match_count": len(matches),
            "total_keywords": len(jd_keywords),
            "matches": list(matches),
            "missing": list(missing)
        }

class SemanticScorer(BaseScorer):
    def score(self, resume_text: str, jd_text: str) -> Dict[str, Any]:
        model = get_embedding_model()
        
        # Compute embeddings
        # Clean text slightly differently? Standard processor is fine.
        processor = TextProcessor()
        clean_resume = processor.clean_text(resume_text)
        clean_jd = processor.clean_text(jd_text)

        emb1 = model.encode(clean_resume, convert_to_tensor=True)
        emb2 = model.encode(clean_jd, convert_to_tensor=True)

        cosine_score = util.cos_sim(emb1, emb2).item()
        
        # Normalize -1 to 1 into 0 to 100
        # Sim usually 0.0 to 1.0 for these sentences anyway
        final_score = max(0.0, min(1.0, cosine_score)) * 100
        
        return {
            "score": round(final_score, 1)
        }

class FormattingScorer(BaseScorer):
    def score(self, resume_text: str, jd_text: str) -> Dict[str, Any]:
        issues = []
        score = 100
        
        # Length check (heuristic: too short implies incomplete, too long implies verbose)
        word_count = len(resume_text.split())
        if word_count < 200:
            score -= 20
            issues.append("Resume might be too short (<200 words).")
        elif word_count > 1500:
            score -= 10
            issues.append("Resume might be too long (>1500 words).")

        # Section check
        sections = ['experience', 'education', 'skills', 'projects']
        lower_text = resume_text.lower()
        missing_sections = []
        for sec in sections:
            if sec not in lower_text:
                score -= 10
                missing_sections.append(sec.title())
        
        if missing_sections:
            issues.append(f"Missing standard sections: {', '.join(missing_sections)}")

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

    def analyze(self, resume_text: str, jd_text: str) -> Dict[str, Any]:
        k_res = self.keyword_scorer.score(resume_text, jd_text)
        s_res = self.semantic_scorer.score(resume_text, jd_text)
        f_res = self.formatting_scorer.score(resume_text, jd_text)
        
        # LLM Analysis
        ai_res = self.llm_service.get_analysis(resume_text, jd_text)

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

