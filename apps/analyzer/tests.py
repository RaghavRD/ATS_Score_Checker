from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from .services.parser import parse_resume
import os

class ParserTests(TestCase):
    def setUp(self):
        # Create a dummy docx if not exists, but we already have test_resume.docx in root.
        # Tests run in a temporary DB but file access is fine.
        # We need the absolute path.
        self.resume_path = os.path.join(os.getcwd(), 'test_resume.docx')

    def test_docx_parsing(self):
        if not os.path.exists(self.resume_path):
            self.fail("test_resume.docx not found")
        
        with open(self.resume_path, 'rb') as f:
            uploaded_file = SimpleUploadedFile('resume.docx', f.read())
            text = parse_resume(uploaded_file)
            self.assertIn('John Doe', text)
            self.assertIn('Python Developer', text)
