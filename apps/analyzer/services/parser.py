import logging
import pdfplumber
import docx
from django.core.files.uploadedfile import UploadedFile
from .text_process import SectionExtractor

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

def parse_resume(file: UploadedFile) -> dict:
    """
    Extracts text and sections from an uploaded resume file (PDF or DOCX).
    Returns: {'full_text': str, 'sections': dict}
    """
    filename = file.name.lower()
    
    # Reset pointer just in case
    file.seek(0)

    text = ""
    if filename.endswith('.pdf'):
        text = extract_text_from_pdf(file)
    elif filename.endswith('.docx'):
        text = extract_text_from_docx(file)
    elif filename.endswith('.doc'):
        raise ValueError("Old .doc format is not supported. Please convert to .docx or .pdf")
    else:
        raise ValueError("Unsupported file format. Please upload PDF or DOCX.")
        
    # Extract sections
    extractor = SectionExtractor()
    sections = extractor.extract_sections(text)
    
    return {
        "full_text": text,
        "sections": sections
    }
