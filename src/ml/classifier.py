import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report, accuracy_score
from src.search.processor import TextProcessor

class DocumentClassifier:
    def __init__(self):
        self.processor = TextProcessor()
        # REQ-B41: Implement Multinomial Naïve Bayes
        # Um alpha menor ajuda o modelo a ser mais sensível a termos raros
        self.model = MultinomialNB(alpha=0.1)
        self.vectorizer = TfidfVectorizer(max_features=5000)
        self.categories_map = {
    'AI & Robotics': [
        'intelligence', 'ia', 'inteligência', 'robótica', 'robot', 
        'automation', 'automação', 'cognitive', 'cognitivo', 'aprendizagem'
    ],
    'Systems & Tech': [
        'vehicle', 'veículo', 'driver', 'condutor', 'adas', 'transport', 
        'software', 'desenvolvimento', 'sistemas', 'network', 'rede'
    ],
    'Education & Society': [
        'learning', 'students', 'estudantes', 'ensino', 'university', 
        'universidade', 'escola', 'education', 'educação'
    ],
    'Data Science': [
        'data', 'dados', 'analytics', 'processing', 'processamento', 
        'estatística', 'model', 'modelo', 'algorithm', 'algoritmo'
    ]
}

    def _assign_label(self, keywords):
        """Atribui uma categoria baseada nas keywords para treino (Ground Truth)."""
        text_keywords = " ".join(keywords).lower()
        for category, terms in self.categories_map.items():
            if any(term in text_keywords for term in terms):
                return category
        return 'General Engineering'

    def prepare_and_train(self, documents):
        """REQ-B42: Train classifier on research publication categories."""
        texts = []
        labels = []

        for doc in documents.values():
            # X: Texto do abstract e título
            text = f"{doc.get('title', '')} {doc.get('abstract', '')}"
            texts.append(text)
            
            # Y: Categoria baseada nas keywords
            label = self._assign_label(doc.get('keywords', []))
            labels.append(label)

        # Vetorização (Transformar texto em números)
        X = self.vectorizer.fit_transform(texts)
        y = np.array(labels)

        from collections import Counter
        print(f" Distribuição das categorias: {Counter(labels)}")

        # REQ-B44: Dividir para avaliação (80% treino, 20% teste)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Treino
        self.model.fit(X_train, y_train)

        # Avaliação
        y_pred = self.model.predict(X_test)
        print("\n---  PERFORMANCE DO CLASSIFICADOR (REQ-B44) ---")
        print(classification_report(y_test, y_pred, zero_division=0))
        return accuracy_score(y_test, y_pred)

    def predict_category(self, title, abstract):
        """REQ-B43: Categorize documents into subject areas automatically."""
        text = f"{title} {abstract}"
        vec = self.vectorizer.transform([text])
        return self.model.predict(vec)[0]