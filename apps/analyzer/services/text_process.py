import re
import string
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Ensure resources are downloaded (can be moved to startup/apps.py ideally, but safe here for now)
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)

class TextProcessor:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))

    def clean_text(self, text: str) -> str:
        """
        Lowercases, removes special characters (keeping basics), and extra whitespace.
        Used for embedding generation.
        """
        if not text:
            return ""
        
        # Lowercase
        text = text.lower()
        
        # Remove special characters but keep some structural punctuation for sentence boundaries if needed
        # For pure keywords, we might want to be aggressive.
        # For embeddings, sentences matter.
        # Let's do a general clean.
        text = re.sub(r'[^a-zA-Z0-9\s.,]', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def extract_keywords(self, text: str) -> set[str]:
        """
        Tokenizes and removes stopwords to return a set of potential keywords.
        """
        text = self.clean_text(text)
        # Remove punctuation for keyword set
        text_no_punct = text.translate(str.maketrans('', '', string.punctuation))
        tokens = word_tokenize(text_no_punct)
        
        keywords = {
            word for word in tokens 
            if word not in self.stop_words and len(word) > 1
        }
        return keywords

class SectionExtractor:
    """
    Heuristic-based extractor to split resume text into logical sections.
    """
    
    SECTION_HEADERS = {
        'experience': [
            r'experience', r'work history', r'work experience', r'employment', 
            r'professional experience', r'career history'
        ],
        'education': [
            r'education', r'academic background', r'qualifications', r'academic history'
        ],
        'skills': [
            r'skills', r'technical skills', r'technologies', r'core competencies', 
            r'proficiencies', r'stack'
        ],
        'projects': [
            r'projects', r'personal projects', r'side projects', r'key projects'
        ],
        'summary': [
            r'summary', r'professional summary', r'profile', r'objective', r'about me'
        ]
    }

    def extract_sections(self, text: str) -> dict[str, str]:
        """
        Splits text into sections based on known headers.
        Returns a dictionary with keys: experience, education, skills, projects, summary, uncategorized.
        """
        lines = text.split('\n')
        sections = {
            'experience': [],
            'education': [],
            'skills': [],
            'projects': [],
            'summary': [],
            'uncategorized': []
        }
        
        current_section = 'uncategorized'
        
        for line in lines:
            clean_line = line.strip().lower()
            if not clean_line:
                continue
                
            # Check if line is a header
            is_header = False
            for section_name, patterns in self.SECTION_HEADERS.items():
                # A header is usually short (less than 6 words)
                if len(clean_line.split()) < 6:
                    for pattern in patterns:
                        # Exact match or match with colon (e.g. "Experience:")
                        if re.match(f"^{pattern}:?$", clean_line):
                            current_section = section_name
                            is_header = True
                            break
                if is_header:
                    break
            
            if not is_header:
                sections[current_section].append(line.strip())
        
        # Join lists back into strings
        return {k: "\n".join(v) for k, v in sections.items()}
