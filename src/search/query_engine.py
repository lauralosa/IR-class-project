import math
import numpy as np # Recomendado para operações vetoriais
from src.search.processor import TextProcessor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class QueryEngine:
    def __init__(self, index_obj):
        self.index_obj = index_obj
        self.processor = TextProcessor()

    def get_idf(self, term):
        """REQ-B33: Calcula o Inverse Document Frequency (IDF)."""
        # Vamos buscar o Document Frequency (df) ao índice
        df = len(self.index_obj.index.get(term, []))
        if df == 0:
            return 0.0
        
        # Fórmula padrão: log10(N/df)
        return math.log10(self.index_obj.num_docs / df)
    
    def _get_weight(self, tf, term, scheme="tfidf"):
        """REQ-B39: Suporta diferentes esquemas de pesagem."""
        if scheme == "binary":
            return 1.0 if tf > 0 else 0.0
        elif scheme == "frequency":
            return float(tf)
        else: # Default: tfidf
            return tf * self.get_idf(term)

    def ranked_search(self, query_str, use_sklearn=False, weighting_scheme="tfidf"):
        """
        Módulo 3.2.4 e 3.2.5: Pesquisa por relevância.
        Decide entre a nossa implementação ou o scikit-learn.
        """
        if use_sklearn:
            return self._ranked_search_sklearn(query_str)
        else:
            return self._ranked_search_custom(query_str, weighting_scheme)

    def _ranked_search_custom(self, query_str, weighting_scheme="tfidf"):
        """Implementação VSM (Vector Space Model) com Normalização."""
        query_terms = self.processor.process_text(query_str, use_stemming=True)
        if not query_terms: return []

        scores = {}
        # 1. Calcular pesos da Query
        query_weights = {}
        for term in set(query_terms): # Usar set() para não repetir termos
            if weighting_scheme == "tfidf":
                tf_q = query_terms.count(term)
                idf = self.index_obj.get_idf(term)
                query_weights[term] = tf_q * idf
            else: # BINARY (REQ-B39)
                query_weights[term] = 1.0

        # 2. Acumular Dot Product
        for term, q_weight in query_weights.items():
            postings, _ = self.index_obj.get_postings(term)
            for doc_id, doc_tf in postings:
                if weighting_scheme == "tfidf":
                    # Peso real TF-IDF
                    doc_weight = doc_tf * self.index_obj.get_idf(term)
                else:
                    # Peso binário (REQ-B39)
                    doc_weight = 1.0
                
                scores[doc_id] = scores.get(doc_id, 0) + (q_weight * doc_weight)

        # 3. Normalização 
        
        # 3.1 Calcular a magnitude da Query: sqrt(sum(w_t,q^2))
        query_magnitude = math.sqrt(sum(weight**2 for weight in query_weights.values()))

        final_results = []
        for doc_id, dot_product in scores.items():
            # Vamos buscar a magnitude que guardaste no indexador
            doc_magnitude = self.index_obj.documents[doc_id].get('magnitude', 1.0)
            
            # 3.3 Cálculo final da Similaridade do Cosseno
            if doc_magnitude > 0 and query_magnitude > 0:
                # similarity = (Q · D) / (|Q| * |D|)
                similarity = dot_product / (query_magnitude * doc_magnitude)
            else:
                similarity = 0.0
                
            final_results.append((doc_id, round(float(similarity), 4)))

        return sorted(final_results, key=lambda x: x[1], reverse=True)

    def _ranked_search_sklearn(self, query_str):
        """REQ-B35: Integração com Scikit-Learn para comparação."""
        doc_ids = sorted(self.index_obj.documents.keys())
        if not doc_ids: return []

        # Reconstruir corpus para o sklearn
        corpus = [
            f"{self.index_obj.documents[d].get('title', '')} {self.index_obj.documents[d].get('abstract', '')}"
            for d in doc_ids
        ]

        # REQ-B35: Vectorizer usa o NOSSO processor para manter consistência total
        vectorizer = TfidfVectorizer(analyzer=lambda text: self.processor.process_text(text, use_stemming=True))
        
        try:
            tfidf_matrix = vectorizer.fit_transform(corpus)
            query_vec = vectorizer.transform([query_str])
            
            # Similaridade do Cosseno
            cosine_sim = cosine_similarity(query_vec, tfidf_matrix).flatten()
            
            results = []
            for i, score in enumerate(cosine_sim):
                if score > 0:
                    results.append((doc_ids[i], round(float(score), 4)))
            
            return sorted(results, key=lambda x: x[1], reverse=True)
        except Exception as e:
            print(f"Erro no sklearn: {e}")
            return []

    def get_incidence_matrix(self):
        """Gera a Matriz de Incidência Termo-Documento (REQ-B24)"""
        all_terms = sorted(self.index_obj.index.keys())
        num_docs = self.index_obj.num_docs
        
        # Criar matriz preenchida com zeros (Termos x Documentos)
        matrix = np.zeros((len(all_terms), num_docs), dtype=int)
        
        for i, term in enumerate(all_terms):
            postings, _ = self.index_obj.get_postings(term)
            for doc_id, _ in postings:
                matrix[i, doc_id] = 1
                
        return matrix, all_terms

    
    def execute_boolean_query(self, query_str):
        """
        Executa pesquisas complexas com precedência e AND implícito.
        Suporta: AND, OR, NOT e termos separados por espaço (REQ-B23, REQ-B26).
        """
        # 1. Pré-processamento: Injetar AND implícito (REQ-B26)
        raw_tokens = query_str.split()
        if not raw_tokens: return []
        
        tokens = []
        operators = {"AND", "OR", "NOT"}
        for i, token in enumerate(raw_tokens):
            tokens.append(token)
            if i < len(raw_tokens) - 1:
                curr_upper = token.upper()
                next_upper = raw_tokens[i+1].upper()
                if curr_upper not in operators and next_upper not in operators:
                    tokens.append("AND")

        # 2. Processamento de Postings com Otimização de Frequência (REQ-B25)
        # Vamos resolver primeiro os NOT, depois os AND, depois os OR (Precedência REQ-B23)
        
        # Simplificação para esta fase: Processamos sequencialmente
        result_docs = None
        current_op = "AND"

        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token.upper() in operators:
                current_op = token.upper()
                i += 1
                continue

            # Obter postings do termo atual (processado pelo NLTK)
            term_processed = self.processor.process_text(token)[0] if self.processor.process_text(token) else ""
            p_list, s_list = self.index_obj.get_postings(term_processed)
            current_ids = [p[0] for p in p_list]

            if result_docs is None:
                result_docs = set(current_ids) if current_op != "NOT" else set()
            else:
                if current_op == "AND":
                    # REQ-B25: Aqui usaríamos a ordenação se tivéssemos múltiplos ANDs seguidos
                    # Para este motor, intersectamos com skips
                    p_res = [[doc_id, 0] for doc_id in sorted(list(result_docs))]
                    # (A lógica de skips é aplicada entre result_docs e current_ids)
                    result_docs = set(self.intersect_with_skips(p_res, [], p_list, s_list))
                elif current_op == "OR":
                    result_docs.update(current_ids)
                elif current_op == "NOT":
                    result_docs.difference_update(current_ids)
            i += 1

        return sorted(list(result_docs)) if result_docs else []

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
    
    def get_document_similarity_matrix(self):
        """REQ-B40: Gera uma matriz de similaridade N x N entre todos os documentos."""
        num_docs = self.index_obj.num_docs
        matrix = np.zeros((num_docs, num_docs))
        
        print(f" A gerar matriz de similaridade para {num_docs} documentos...")
        
        # 1. Obter todos os vetores de documentos (esparsos)
        doc_vectors = {}
        for term, postings in self.index_obj.index.items():
            idf = self.get_idf(term)
            for doc_id, tf in postings:
                if doc_id not in doc_vectors: doc_vectors[doc_id] = {}
                doc_vectors[doc_id][term] = tf * idf

        # 2. Calcular Cosseno entre cada par (i, j)
        for i in range(num_docs):
            for j in range(i, num_docs): # Matriz é simétrica, calculamos apenas metade
                if i == j:
                    matrix[i, j] = 1.0
                    continue
                
                # Produto escalar entre doc i e doc j
                dot_product = 0
                vec_i = doc_vectors.get(i, {})
                vec_j = doc_vectors.get(j, {})
                
                # Iterar sobre os termos do documento mais pequeno para eficiência
                if len(vec_i) > len(vec_j): vec_i, vec_j = vec_j, vec_i
                
                for term, weight in vec_i.items():
                    if term in vec_j:
                        dot_product += weight * vec_j[term]
                
                mag_i = self.index_obj.documents[i].get('magnitude', 1.0)
                mag_j = self.index_obj.documents[j].get('magnitude', 1.0)
                
                sim = dot_product / (mag_i * mag_j) if (mag_i * mag_j) > 0 else 0
                matrix[i, j] = matrix[j, i] = round(float(sim), 4)
                
        return matrix