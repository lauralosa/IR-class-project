import math
import numpy as np # Recomendado para operações vetoriais
from src.search.processor import TextProcessor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class QueryEngine:
    def __init__(self, index_obj):
        self.index_obj = index_obj
        self.processor = TextProcessor()

    def ranked_search(self, query_str, use_sklearn=False):
        """
        Módulo 3.2.4 e 3.2.5: Pesquisa por relevância.
        Decide entre a nossa implementação ou o scikit-learn.
        """
        if use_sklearn:
            return self._ranked_search_sklearn(query_str)
        else:
            return self._ranked_search_custom(query_str)

    def _ranked_search_custom(self, query_str):
        """Implementação VSM (Vector Space Model) com Normalização."""
        query_terms = self.processor.process_text(query_str, use_stemming=True)
        if not query_terms: return []

        scores = {}
        # 1. Calcular pesos da Query (TF-IDF simples para a query)
        query_weights = {}
        for term in query_terms:
            query_weights[term] = query_weights.get(term, 0) + 1
        
        for term, q_tf in query_weights.items():
            idf = self.index_obj.get_idf(term)
            query_weights[term] = q_tf * idf

        # 2. Acumular Dot Product
        for term, q_weight in query_weights.items():
            postings, _ = self.index_obj.get_postings(term)
            for doc_id, doc_tf in postings:
                # w_td = doc_tf * idf
                scores[doc_id] = scores.get(doc_id, 0) + (q_weight * (doc_tf * idf))

        # 3. Normalização (Requisito Crítico 3.2.4)
        # Nota: Assume que o index_obj já tem o cálculo de magnitude de cada doc
        final_results = []
        for doc_id, dot_product in scores.items():
            # magnitude = self.index_obj.get_doc_magnitude(doc_id) 
            # similarity = dot_product / magnitude
            final_results.append((doc_id, dot_product)) 

        return sorted(final_results, key=lambda x: x[1], reverse=True)

    def _ranked_search_sklearn(self, query_str):
        """Integração com sklearn e Similaridade do Cosseno (Requisito 3.2.4)."""
        doc_ids = list(self.index_obj.documents.keys())
        if not doc_ids:
            return []

        # Criar o corpus com os documentos atuais
        corpus = []
        for d_id in doc_ids:
            doc = self.index_obj.documents[d_id]
            corpus.append(f"{doc.get('title', '')} {doc.get('abstract', '')}")

        # Vectorizer usa o nosso processador para manter a consistência (stemming/stopwords)
        vectorizer = TfidfVectorizer(analyzer=lambda text: self.processor.process_text(text, use_stemming=True))
        
        try:
            tfidf_matrix = vectorizer.fit_transform(corpus)
            query_vec = vectorizer.transform([query_str])
            
            # Cálculo da Similaridade do Cosseno
            cosine_sim = cosine_similarity(query_vec, tfidf_matrix).flatten()
            
            results = []
            for i, score in enumerate(cosine_sim):
                if score > 0:
                    results.append((doc_ids[i], float(score)))
            
            return sorted(results, key=lambda x: x[1], reverse=True)
        except:
            return []

    def execute_boolean_query(self, query_str, operator="AND"):
        """Módulo 3.2.2: Pesquisa Booleana com suporte a Skip Pointers."""
        query_terms = self.processor.process_text(query_str, use_stemming=True)
        
        if not query_terms:
            return []

        if len(query_terms) < 2:
            postings, _ = self.index_obj.get_postings(query_terms[0])
            return [p[0] for p in postings]

        p1, s1 = self.index_obj.get_postings(query_terms[0])
        p2, s2 = self.index_obj.get_postings(query_terms[1])

        if operator.upper() == "AND":
            return self.intersect_with_skips(p1, s1, p2, s2)
        elif operator.upper() == "OR":
            return self.union(p1, p2)
        elif operator.upper() == "NOT":
            return self.difference(p1, p2)
        
        return []

    def intersect_with_skips(self, p1, s1, p2, s2):
        """Versão rigorosa da interseção otimizada."""
        answer = []
        i, j = 0, 0
        skip_interval_1 = round(math.sqrt(len(p1)))
        skip_interval_2 = round(math.sqrt(len(p2)))

        while i < len(p1) and j < len(p2):
            if p1[i][0] == p2[j][0]:
                answer.append(p1[i][0])
                i += 1
                j += 1
            elif p1[i][0] < p2[j][0]:
                # Tenta saltar em p1
                if i in s1:
                    next_skip_idx = i + skip_interval_1
                    if next_skip_idx < len(p1) and p1[next_skip_idx][0] <= p2[j][0]:
                        while next_skip_idx < len(p1) and p1[next_skip_idx][0] <= p2[j][0]:
                            i = next_skip_idx
                            next_skip_idx += skip_interval_1
                    else: i += 1
                else: i += 1
            else:
                # Tenta saltar em p2
                if j in s2:
                    next_skip_idx = j + skip_interval_2
                    if next_skip_idx < len(p2) and p2[next_skip_idx][0] <= p1[i][0]:
                        while next_skip_idx < len(p2) and p2[next_skip_idx][0] <= p1[i][0]:
                            j = next_skip_idx
                            next_skip_idx += skip_interval_2
                    else: j += 1
                else: j += 1
        return answer

    def _get_skip_target_index(self, current_pos, skips, postings):
        if current_pos in skips:
            idx_in_skips = skips.index(current_pos)
            if idx_in_skips + 1 < len(skips):
                return skips[idx_in_skips + 1]
        return None

    def union(self, p1, p2):
        ids1 = {p[0] for p in p1}
        ids2 = {p[0] for p in p2}
        return sorted(list(ids1 | ids2))

    def difference(self, p1, p2):
        ids2 = {p[0] for p in p2}
        return [p[0] for p in p1 if p[0] not in ids2]