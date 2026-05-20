import nltk
import string
import logging
from nltk.tokenize import word_tokenize , sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
from src.config import settings

# Descarregar recursos necessários do NLTK (apenas na primeira execução)
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('punkt_tab')
nltk.download('wordnet')
nltk.download('omw-1.4')

# Configuração do Logger para o processador
logger = logging.getLogger("PROCESSOR")

class TextProcessor:
    def __init__(self, language='portuguese'):
        self.language = language
        self.stemmer = PorterStemmer()
        self.lemmatizer = WordNetLemmatizer()
        # REQ-B15: Carregar stop words (Bilingue)
        try:
            self.stop_words = set(stopwords.words('portuguese')).union(set(stopwords.words('english')))
        except:
            logger.warning("Stopwords não encontradas. A descarregar...")
            nltk.download('stopwords')
            self.stop_words = set(stopwords.words('portuguese')).union(set(stopwords.words('english')))

    

    def process_text(self, text, use_stemming=False, use_lemmatization=False, remove_stopwords=True):
        """
        Realiza o pré-processamento do texto
        """
        if not text or text == "N/A":
            return []

        # 1. Normalização (Minusculas) e Tokenização
        tokens = word_tokenize(text.lower())

        # 2. Filtragem de Ruído e Stop Words
        tokens = [t for t in tokens if t.isalpha() and t not in string.punctuation and len(t) > 2]

        # 3. Remoção de Stop Words (REQ-B15)
        if remove_stopwords:
            tokens = [t for t in tokens if t not in self.stop_words]

        # 3. Lematização (REQ-B17) - Prioritária se ativada
        if use_lemmatization:
            # WordNet Lemmatizer reduz "computers" -> "computer"
            tokens = [self.lemmatizer.lemmatize(t) for t in tokens]

        # 5. Redução (Stemming)
        if use_stemming:
            tokens = [self.stemmer.stem(t) for t in tokens]

        return tokens
    
    def add_custom_stop_words(self, words_list):
        """REQ-B20: Permite configurar stop words adicionais específicas do domínio."""
        if isinstance(words_list, list):
            self.stop_words.update([w.lower() for w in words_list])
            logger.info(f"Adicionadas {len(words_list)} stop words customizadas.")