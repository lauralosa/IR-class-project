import math
import numpy as np # Recomendado para operações vetoriais
from src.search.processor import TextProcessor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import wordnet
import re
import json
import os

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

    def ranked_search(self, query_str, use_sklearn=False, weighting_scheme="ltc"):
        """
        REQ-B37 / REQ-F20: Pesquisa por relevância com suporte a esquemas SMART.
        O weighting_scheme recebe strings como 'ltc', 'lnc', 'nnn'.
        """
        if use_sklearn:
            return self._ranked_search_sklearn(query_str)
        else:
            return self._ranked_search_custom(query_str, weighting_scheme)

    def _ranked_search_custom(self, query_str, weighting_scheme="tfidf"):
        """Implementação VSM (Vector Space Model) com suporte a esquemas SMART.
        Default 'ltc': log tf, idf, cosine normalization."""
        # 0. Mapeamento para retrocompatibilidade (se vier "tfidf" ou "binary")
        if weighting_scheme == "tfidf": weighting_scheme = "ltc"
        elif weighting_scheme == "binary": weighting_scheme = "nnn"
        
        # Extrair os componentes do esquema (ex: ltc -> l, t, c)
        tf_type = weighting_scheme[0].lower()
        df_type = weighting_scheme[1].lower()
        norm_type = weighting_scheme[2].lower()

        query_terms = self.processor.process_text(query_str, use_stemming=True)
        if not query_terms: return []
        

        scores = {}
        # 1. Calcular pesos da Query
        query_weights = {}
        for term in set(query_terms): # Usar set() para não repetir termos
            raw_tf_q = query_terms.count(term)
        
            # Componente TF (l ou n)
            tf_q = (1 + math.log10(raw_tf_q)) if tf_type == 'l' and raw_tf_q > 0 else raw_tf_q
            
            # Componente DF/IDF (t ou n)
            idf = self.index_obj.get_idf(term) if df_type == 't' else 1.0
            
            query_weights[term] = tf_q * idf

        # 2. Acumular Dot Product
        for term, q_weight in query_weights.items():
            postings, _ = self.index_obj.get_postings(term)
            for posting in postings:
                doc_id = posting[0]
                positions = posting[1]
                raw_tf_d = len(positions)
                
                # Componente TF do Documento (l ou n)
                tf_d = (1 + math.log10(raw_tf_d)) if tf_type == 'l' and raw_tf_d > 0 else raw_tf_d
                
                # Componente IDF do Documento (t ou n)
                # Nota: O IDF é aplicado no documento se a 2ª letra for 't'
                doc_idf = self.index_obj.get_idf(term) if df_type == 't' else 1.0
                
                doc_weight = tf_d * doc_idf
                
                scores[doc_id] = scores.get(doc_id, 0) + (q_weight * doc_weight)

        # 3. Normalização 
        
        # 3.1 Calcular a magnitude da Query: sqrt(sum(w_t,q^2))
        query_magnitude = math.sqrt(sum(weight**2 for weight in query_weights.values()))

        final_results = []
        for doc_id, dot_product in scores.items():
            # Aceder aos metadados do documento (garantindo que o ID é string se necessário)
            doc_info = self.index_obj.documents.get(doc_id) or self.index_obj.documents.get(str(doc_id))
            doc_magnitude = doc_info.get('magnitude', 1.0) if doc_info else 1.0
            
            # 3.3 Cálculo da Similaridade
            if norm_type == 'c': # Cosseno
                if doc_magnitude > 0 and query_magnitude > 0:
                    # similarity = (Q · D) / (|Q| * |D|)
                    similarity = dot_product / (query_magnitude * doc_magnitude)
                else:
                    similarity = 0.0
            else: # 'n' (Nenhuma normalização - apenas Dot Product bruto)
                similarity = dot_product
                
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

    
    

    def execute_boolean_query(self, query_str, expand=False):
        """
        REQ-B45: Precedência (NOT > AND > OR)
        REQ-B47: Expansão de Query
        REQ-B48: Phrase Queries
        """
        # 1. Extração de Frases ("termo termo") - REQ-B48
        # Substituímos frases entre aspas por um token especial para não as partir no split
        phrases = re.findall(r'"([^"]*)"', query_str)
        for i, p in enumerate(phrases):
            query_str = query_str.replace(f'"{p}"', f'PHRASE_{i}')

        # 2. Tokenização e AND implícito - REQ-B26
        raw_tokens = query_str.split()
        tokens = []
        operators = {"AND", "OR", "NOT"}
        
        for i, token in enumerate(raw_tokens):
            tokens.append(token)
            if i < len(raw_tokens) - 1:
                curr = token.upper()
                nxt = raw_tokens[i+1].upper()
                if curr not in operators and nxt not in operators:
                    tokens.append("AND")

        # 3. Converter para Notação Polaca Inversa (Shunting-yard) - REQ-B45
        # Define a precedência: NOT (3) > AND (2) > OR (1)
        precedence = {"NOT": 3, "AND": 2, "OR": 1}
        output_queue = []
        operator_stack = []

        for token in tokens:
            token_upper = token.upper()
            if token_upper in operators:
                while (operator_stack and operator_stack[-1] in operators and 
                    precedence[operator_stack[-1]] >= precedence[token_upper]):
                    output_queue.append(operator_stack.pop())
                operator_stack.append(token_upper)
            else:
                output_queue.append(token)
        
        while operator_stack:
            output_queue.append(operator_stack.pop())

        # 4. Avaliação da Query usando uma Pilha
        results_stack = []
        all_doc_ids = set(self.index_obj.documents.keys())

        for token in output_queue:
            if token == "NOT":
                s1 = results_stack.pop()
                results_stack.append(all_doc_ids - s1)
            elif token == "AND":
                s2, s1 = results_stack.pop(), results_stack.pop()
                results_stack.append(s1 & s2)
            elif token == "OR":
                s2, s1 = results_stack.pop(), results_stack.pop()
                results_stack.append(s1 | s2)
            else:
                # É um termo ou uma frase
                if token.startswith("PHRASE_"):
                    # Resolver Frase - REQ-B48
                    idx = int(token.split("_")[1])
                    phrase_raw = phrases[idx]
                    phrase_terms = self.processor.process_text(phrase_raw)
                    results_stack.append(set(self.search_phrase(phrase_terms)))
                else:
                    # Resolver Termo Único com Expansão Opcional - REQ-B47
                    processed = self.processor.process_text(token)
                    term = processed[0] if processed else ""
                    
                    # Se expand=True, buscamos sinónimos
                    terms_to_search = [term]
                    if expand and term:
                        terms_to_search = self.expand_query([term])
                    
                    # Unimos os resultados de todos os sinónimos (OR entre eles)
                    term_results = set()
                    for t in terms_to_search:
                        p_list, _ = self.index_obj.get_postings(t)
                        term_results.update([p[0] for p in p_list])
                    results_stack.append(term_results)

        return sorted(list(results_stack[0])) if results_stack else []

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

    def search_phrase(self, terms):
        """REQ-B48: Procura por uma frase exata usando posições."""
        if not terms: return []
        
        # 1. Obter postings para todos os termos
        postings_list = []
        for term in terms:
            p, _ = self.index_obj.get_postings(term)
            if not p: return [] # Se um termo não existe, a frase não existe
            postings_list.append(dict(p)) # Convertemos para dicionário {doc_id: [pos]}

        # 2. Intersetar documentos que contêm todos os termos
        common_docs = set(postings_list[0].keys())
        for p_dict in postings_list[1:]:
            common_docs &= set(p_dict.keys())

        # 3. Verificar contiguidade (posições seguidas)
        results = []
        for doc_id in common_docs:
            # Pegamos nas posições do primeiro termo
            possible_starts = postings_list[0][doc_id]
            
            for start_pos in possible_starts:
                is_match = True
                for i in range(1, len(terms)):
                    next_term_positions = postings_list[i][doc_id]
                    # O próximo termo tem de estar na posição (start_pos + i)
                    if (start_pos + i) not in next_term_positions:
                        is_match = False
                        break
                
                if is_match:
                    results.append(doc_id)
                    break # Encontramos a frase neste doc, passamos ao próximo doc

        return sorted(list(set(results)))
    
    def expand_query(self, query_terms):
        """REQ-B47: Expande a query com sinónimos para aumentar o Recall."""
        expanded = set(query_terms)
        for term in query_terms:
            syns = wordnet.synsets(term)
            for syn in syns:
                for lemma in syn.lemmas():
                    synonym = lemma.name().replace('_', ' ').lower()
                    # Apenas adicionamos sinónimos de uma palavra para não complicar
                    if ' ' not in synonym:
                        expanded.add(synonym)
        return list(expanded)

    

    

    def generate_snippet(self, doc_id, query_terms, window_chars=150):
        doc = self.index_obj.documents.get(doc_id) or self.index_obj.documents.get(str(doc_id))
        if not doc: return ""

        # 1. Tentar ler o texto literal (TXT) em vez dos tokens (JSON)
        # Convertemos: data\processed_text\doc_11.json -> data\extracted_text\doc_11.txt
        proc_path = doc.get('processed_text_path', "")
        raw_text_path = proc_path.replace('processed_text', 'extracted_text').replace('.json', '.txt')
        
        content = ""
        if os.path.exists(raw_text_path):
            try:
                with open(raw_text_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                    # --- A LIMPEZA ACONTECE AQUI ---
                    # 1. Substitui quebras de linha (\n ou \r) por espaços
                    content = content.replace('\n', ' ').replace('\r', ' ')
                    # 2. Transforma múltiplos espaços seguidos em apenas um
                    content = re.sub(r'\s+', ' ', content)
                    # 3. Limpa sequências de pontos excessivas (ex: . . . . .)
                    content = re.sub(r'\.\s?\.\s?\.\s?', '...', content)
                    # -------------------------------
            except Exception as e:
                print(f"Erro ao ler TXT: {e}")
        
        # Fallback para o abstract se o TXT falhar
        if not content:
            content = doc.get('abstract', '')

        # 2. Procurar o termo da query no texto literal
        # Procuramos a posição de um dos termos (usando regex para ignorar case)
        match_pos = -1
        found_term = ""
        
        for term in query_terms:
            # Procuramos o termo ou o seu início (por causa do stemming)
            # Usamos re.search para encontrar a posição da palavra no texto original
            match = re.search(rf'\b{re.escape(term[:4])}\w*', content, re.IGNORECASE)
            if match:
                match_pos = match.start()
                found_term = match.group()
                break

        # 3. Criar a janela de visualização baseada em caracteres (fica mais bonito)
        if match_pos != -1:
            start = max(0, match_pos - window_chars)
            end = min(len(content), match_pos + window_chars)
            
            snippet = content[start:end]
            
            # 4. Highlight: Meter em negrito no texto original
            # Substituímos todas as ocorrências dos termos da query por eles mesmos entre <b>
            for term in query_terms:
                pattern = rf'(\b{re.escape(term[:4])}\w*)'
                snippet = re.sub(pattern, r'<b>\1</b>', snippet, flags=re.IGNORECASE)
                
            return ("... " if start > 0 else "") + snippet + (" ..." if end < len(content) else "")

        return content[:250] + "..."