import logging
import pdfplumber
import docx
from django.core.files.uploadedfile import UploadedFile

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_stream) -> str:
    text = ""
    try:
        with pdfplumber.open(file_stream) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        logger.error(f"Error parsing PDF: {e}")
        raise ValueError("Failed to process PDF.")
    return text

def extract_text_from_docx(file_stream) -> str:
    try:
        doc = docx.Document(file_stream)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        logger.error(f"Error parsing DOCX: {e}")
        raise ValueError("Failed to process DOCX.")

def parse_resume(file: UploadedFile) -> str:
    """
    Extracts text from an uploaded resume file (PDF or DOCX).
    """
    filename = file.name.lower()
    
    # Reset pointer just in case
    file.seek(0)

    if filename.endswith('.pdf'):
        return extract_text_from_pdf(file)
    elif filename.endswith('.docx'):
        return extract_text_from_docx(file)
    elif filename.endswith('.doc'):
        raise ValueError("Old .doc format is not supported. Please convert to .docx or .pdf")
    else:
        raise ValueError("Unsupported file format. Please upload PDF or DOCX.")
