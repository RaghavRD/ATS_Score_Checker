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
