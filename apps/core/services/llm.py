import os
import json
import logging
from typing import Dict, Any, List
from openai import OpenAI
from django.conf import settings

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.grok_key = os.getenv("GROK_API_KEY") # Handling user typo 'GROK' for Groq
        
        self.client = None
        self.model = "gpt-4o-mini"

        if self.grok_key and self.grok_key.startswith("gsk_"):
            # Groq Cloud Configuration
            self.client = OpenAI(
                api_key=self.grok_key,
                base_url="https://api.groq.com/openai/v1"
            )
            self.model = "llama-3.3-70b-versatile"
            logger.info("Using Groq API (Llama 3.3).")
        elif self.openai_key:
            # OpenAI Configuration
            self.client = OpenAI(api_key=self.openai_key)
            logger.info("Using OpenAI API.")
        else:
            logger.warning("No valid API Key found (checked OPENAI_API_KEY and GROK_API_KEY). Running in MOCK mode.")

    def get_analysis(self, resume_text: str, jd_text: str) -> Dict[str, Any]:
        """
        Generates qualitative feedback and structured data using LLM.
        """
        if not self.client:
            return self._get_mock_response()

        prompt = self._build_prompt(resume_text, jd_text)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert ATS and Recruiter. Analyze the resume against the job description. Return valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            logger.error(f"LLM API Error: {e}")
            return self._get_error_response()

    def _build_prompt(self, resume: str, jd: str) -> str:
        # Truncate to reasonable limits to avoid token overflow issues on small limits
        return f"""
        Analyze the following Resume against the Job Description.

        JOB DESCRIPTION:
        {jd[:3000]}

        RESUME:
        {resume[:3000]}

        Provide a strict JSON output with the following keys and NO markdown formatting:
        {{
            "summary": "A brief 1-2 sentence professional summary of the fit.",
            "strengths": ["List of 3 key strengths found in the resume relevant to this job"],
            "missing_skills": ["List of important skills from JD missing in resume"],
            "suggestions": ["List of 3 specific actionable improvements for the resume"],
            "experience_rating": "One of: Low, Medium, High, Perfect"
        }}
        """

    def _get_mock_response(self) -> Dict[str, Any]:
        return {
            "summary": "This is a MOCK analysis because NO API KEY was found. The resume appears to be a good fit but we cannot generate real insights.",
            "strengths": ["Mock Strength 1", "Mock Strength 2", "Mock Strength 3"],
            "missing_skills": ["Real API Key", "Configuration"],
            "suggestions": [
                "Add OPENAI_API_KEY to your .env file to enable real AI analysis.",
                "Detail your experience with AI integration.",
                "Quantify your achievements."
            ],
            "experience_rating": "Medium"
        }

    def _get_error_response(self) -> Dict[str, Any]:
        return {
            "summary": "AI Analysis failed due to an error.",
            "strengths": [],
            "missing_skills": [],
            "suggestions": ["Please try again later or check your API Key."],
            "experience_rating": "Unknown"
        }
