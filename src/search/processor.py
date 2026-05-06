import nltk
import string
from nltk.tokenize import word_tokenize , sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer

# Descarregar recursos necessários do NLTK (apenas na primeira execução)
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('punkt_tab')
nltk.download('wordnet')
nltk.download('omw-1.4')

class TextProcessor:
    def __init__(self, language='portuguese'):
        self.language = language
        self.stemmer = PorterStemmer()
        self.lemmatizer = WordNetLemmatizer()
        # Carregar stop words para português e inglês
        self.stop_words = set(stopwords.words('portuguese')).union(set(stopwords.words('english')))

    

    def process_text(self, text, use_stemming=True, use_lemmatization=False, remove_stopwords=True):
        """
        Realiza o pré-processamento do texto
        """
        if not text or text == "N/A":
            return []

        # 1. Segmentação de Frases (REQ-B14)
        # Útil para processamento gramatical futuro ou sumariação
        sentences = sent_tokenize(text) 
        
        # 2. Tokenização e Normalização
        tokens = word_tokenize(text.lower())

        # 3. Filtragem de Ruído (Crucial para reduzir os 53k termos)
        # Mantemos apenas palavras (isalpha) e com mais de 2 caracteres
        tokens = [t for t in tokens if t.isalpha() and t not in string.punctuation and len(t) > 2]

        # 4. Remoção de Stop Words (REQ-B15)
        tokens = [t for t in tokens if t not in self.stop_words]

        # 5. Redução (Stemming)
        if use_stemming:
            tokens = [self.stemmer.stem(t) for t in tokens]

        return tokens