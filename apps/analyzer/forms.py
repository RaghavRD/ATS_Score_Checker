from django import forms

class UploadResumeForm(forms.Form):
    job_description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Paste Job Description here...'}),
        label="Job Description",
        required=True
    )
    resume = forms.FileField(
        label="Upload Resume (PDF/DOCX)",
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        required=True
    )
