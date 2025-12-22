from django.db import models

from django.contrib.auth.models import User

class AnalysisResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    job_description_snippet = models.TextField(help_text="Snippet of JD for reference")
    resume_filename = models.CharField(max_length=255)
    
    # Scores
    final_score = models.FloatField()
    keyword_score = models.FloatField()
    semantic_score = models.FloatField()
    formatting_score = models.FloatField()
    
    # JSON Data (Full Breakdown & AI Feedback)
    # Using JSONField if supported (SQLite supports it in recent Django versions)
    # Otherwise TextField with json dumps
    data = models.JSONField(default=dict)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.resume_filename} - {self.final_score}% ({self.created_at.strftime('%Y-%m-%d')})"
