import nltk
import string
from nltk.tokenize import word_tokenize
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

        # 1. Tokenização e conversão para minúsculas
        tokens = word_tokenize(text.lower())

        # 2. Remoção de pontuação
        tokens = [t for t in tokens if t not in string.punctuation]

        # 3. Remoção de Stop Words (Configurável)
        if remove_stopwords:
            tokens = [t for t in tokens if t not in self.stop_words]

        # 4. Stemming ou Lematização (Configurável)
        if use_stemming:
            tokens = [self.stemmer.stem(t) for t in tokens]
        elif use_lemmatization:
            tokens = [self.lemmatizer.lemmatize(t) for t in tokens]

        return tokens