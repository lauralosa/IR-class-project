import math
import numpy as np 
import logging
from src.search.processor import TextProcessor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import wordnet
import re
import json
import os
from src.config import settings

# Configuração do Logger 
logger = logging.getLogger("QUERY-ENGINE")

class QueryEngine:
    def __init__(self, index_obj):
        self.index_obj = index_obj
        self.processor = TextProcessor()
        logger.info("QueryEngine inicializado.")

    def get_idf(self, term):
        """Calcula o IDF delegado ao index_obj para garantir mesma suavização."""
        return self.index_obj.get_idf(term)
    
    def _get_weight(self, tf, term, scheme="tfidf"):
        """REQ-B39: Suporta diferentes esquemas de pesagem."""
        if scheme == "binary":
            return 1.0 if tf > 0 else 0.0
        elif scheme == "frequency":
            return float(tf)
        else: # Default: tfidf
            return tf * self.get_idf(term)

    def ranked_search(self, query_str, use_sklearn=False, weighting_scheme="ltc", 
                      use_stemming=None, use_lemmatization=None, remove_stopwords=True, 
                      scope="all"):
        """
        REQ-B37 / REQ-F20: Pesquisa por relevância com suporte a esquemas SMART.
        O weighting_scheme recebe strings como 'ltc', 'lnc', 'nnn'.
        """
        # Se os parâmetros de NLP forem None, usamos a estratégia original do índice (REQ-F52)
        idx_strategy = self.index_obj.metadata.get('reduction_strategy', 'stemming')
        s = use_stemming if use_stemming is not None else (idx_strategy == 'stemming')
        l = use_lemmatization if use_lemmatization is not None else (idx_strategy == 'lemmatization')

        logger.info(f"Pesquisa iniciada: '{query_str}' [Scope: {scope}] [Method: {'Sklearn' if use_sklearn else 'Custom'}]")

        if use_sklearn:
            return self._ranked_search_sklearn(query_str)
        else:
            return self._ranked_search_custom(query_str, weighting_scheme, s, l, remove_stopwords, scope)

    def _ranked_search_custom(self, query_str, weighting_scheme, s, l, stopwords, scope):
        """Implementação VSM com filtros de escopo."""
        # Normalização de nomes de esquemas
        if weighting_scheme == "tfidf": weighting_scheme = "ltc"
        elif weighting_scheme == "binary": weighting_scheme = "nnn"
        
        # Extrair os componentes do esquema (ex: ltc -> l, t, c)
        tf_type = weighting_scheme[0].lower()
        df_type = weighting_scheme[1].lower()
        norm_type = weighting_scheme[2].lower()

        query_terms = self.processor.process_text(query_str, use_stemming=True, use_lemmatization=l, remove_stopwords=stopwords)
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
                doc_id_int = posting[0]
                doc_id = str(doc_id_int)
                # Correção: Tentar as duas chaves (str ou int) dependendo se foi carregado JSON ou criado fresco
                doc_info = self.index_obj.documents.get(doc_id) or self.index_obj.documents.get(doc_id_int)
                if not doc_info: continue

                # Lógica de Filtro por Escopo (Título / Resumo / Tudo)
                if scope != "all":
                    text_to_check = doc_info.get('title', '').lower() if scope == "title" else doc_info.get('abstract', '').lower()
                    # Verifica se o termo processado existe no campo específico
                    # (Nota: Esta é uma simplificação para os 110 docs)
                    if term not in self.processor.process_text(text_to_check, use_stemming=s, use_lemmatization=l):
                        continue
                
                raw_tf_d = len(posting[1])
                tf_d = (1 + math.log10(raw_tf_d)) if tf_type == 'l' and raw_tf_d > 0 else raw_tf_d
                doc_idf = self.index_obj.get_idf(term) if df_type == 't' else 1.0
                
                scores[doc_id] = scores.get(doc_id, 0) + (q_weight * tf_d * doc_idf)

        # 3. Normalização 
        
        # 3.1 Calcular a magnitude da Query: sqrt(sum(w_t,q^2))
        query_magnitude = math.sqrt(sum(weight**2 for weight in query_weights.values()))
        final_results = []

        for doc_id, dot_product in scores.items():
            # Aceder aos metadados do documento (garantindo que o ID é string se necessário)
            doc_info = self.index_obj.documents.get(doc_id) or self.index_obj.documents.get(str(doc_id))
            if not doc_info and str(doc_id).isdigit():
                doc_info = self.index_obj.documents.get(int(doc_id))
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
        logger.debug(f"Executando query booleana: {query_str}")
        
        # 1. Extração de Frases e Proximidade ("termo termo" ou "termo termo"~N) - REQ-B48
        phrases_data = []
        def replace_phrase(match):
            idx = len(phrases_data)
            phrase_text = match.group(1)
            dist_str = match.group(2)
            dist = int(dist_str) if dist_str else 1
            phrases_data.append((phrase_text, dist))
            return f"PHRASE_{idx}"
            
        query_str = re.sub(r'"([^"]*)"(?:~(\d+))?', replace_phrase, query_str)

        # 2. Tokenização e AND implícito - REQ-B26
        raw_tokens = query_str.split()
        tokens = []
        operators = {"AND", "OR", "NOT"}
        
        for i, token in enumerate(raw_tokens):
            tokens.append(token)
            if i < len(raw_tokens) - 1:
                curr = token.upper()
                nxt = raw_tokens[i+1].upper()
                if curr not in {"AND", "OR", "NOT"} and nxt not in {"AND", "OR"}:
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
        all_doc_ids = set(int(k) if str(k).isdigit() else str(k) for k in self.index_obj.documents.keys())

        for token in output_queue:
            if token == "NOT":
                if not results_stack: continue
                p1, _ = results_stack.pop()
                all_postings = [[doc_id, []] for doc_id in sorted(list(all_doc_ids))]
                diff = self.difference(all_postings, p1)
                results_stack.append((diff, []))
            elif token == "AND":
                if len(results_stack) < 2: continue
                p2, s2 = results_stack.pop()
                p1, s1 = results_stack.pop()
                res = self.intersect_with_skips(p1, s1, p2, s2)
                results_stack.append((res, []))
            elif token == "OR":
                if len(results_stack) < 2: continue
                p2, _ = results_stack.pop()
                p1, _ = results_stack.pop()
                res = self.union(p1, p2)
                results_stack.append((res, []))
            else:
                # É um termo ou uma frase
                if token.startswith("PHRASE_"):
                    # Resolver Frase e Proximidade - REQ-B48
                    idx = int(token.split("_")[1])
                    phrase_raw, max_dist = phrases_data[idx]
                    phrase_terms = self.processor.process_text(phrase_raw)
                    phrase_docs = self.search_phrase(phrase_terms, max_distance=max_dist)
                    dummy_postings = [[doc_id, []] for doc_id in phrase_docs]
                    results_stack.append((dummy_postings, []))
                else:
                    # Resolver Termo Único com Expansão Opcional - REQ-B47
                    processed = self.processor.process_text(token)
                    term = processed[0] if processed else ""
                    
                    if expand and term:
                        terms_to_search = self.expand_query([term])
                        combined_p = []
                        for t in terms_to_search:
                            p_list, _ = self.index_obj.get_postings(t)
                            combined_p = self.union(combined_p, p_list)
                        results_stack.append((combined_p, []))
                    else:
                        p_list, s_list = self.index_obj.get_postings(term)
                        results_stack.append((p_list, s_list))

        if results_stack:
            final_p, _ = results_stack[0]
            return [p[0] for p in final_p]
        return []

    def intersect_with_skips(self, p1, s1, p2, s2):
        """Versão rigorosa da interseção otimizada com skips."""
        answer = []
        if not p1 or not p2: return [] # Segurança contra divisões por zero
        i, j = 0, 0
        skip_interval_1 = round(math.sqrt(len(p1)))
        skip_interval_2 = round(math.sqrt(len(p2)))

        while i < len(p1) and j < len(p2):
            if p1[i][0] == p2[j][0]:
                answer.append([p1[i][0], []]) # Formato de posting
                i += 1
                j += 1
            elif p1[i][0] < p2[j][0]:
                if i in s1 and skip_interval_1 > 0:
                    next_skip_idx = i + skip_interval_1
                    if next_skip_idx < len(p1) and p1[next_skip_idx][0] <= p2[j][0]:
                        while next_skip_idx < len(p1) and p1[next_skip_idx][0] <= p2[j][0]:
                            i = next_skip_idx
                            next_skip_idx += skip_interval_1
                    else: i += 1
                else: i += 1
            else:
                if j in s2 and skip_interval_2 > 0:
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
        return [[doc_id, []] for doc_id in sorted(list(ids1 | ids2))]

    def difference(self, p1, p2):
        ids2 = {p[0] for p in p2}
        return [[p[0], []] for p in p1 if p[0] not in ids2]
    
    def get_document_similarity_matrix(self):
        """REQ-B40: Gera uma matriz de similaridade N x N entre todos os documentos."""
        doc_ids = sorted(list(self.index_obj.documents.keys()))
        num_docs = len(doc_ids)
        doc_id_to_idx = {str(doc_id): i for i, doc_id in enumerate(doc_ids)}
        
        matrix = np.zeros((num_docs, num_docs))
        
        print(f" A gerar matriz de similaridade para {num_docs} documentos...")
        
        # 1. Obter todos os vetores de documentos (esparsos)
        doc_vectors = {}
        for term, postings in self.index_obj.index.items():
            idf = self.get_idf(term)
            for doc_id, pos_list in postings:
                idx = doc_id_to_idx.get(str(doc_id))
                if idx is None: continue
                if idx not in doc_vectors: doc_vectors[idx] = {}
                doc_vectors[idx][term] = len(pos_list) * idf

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
                
                real_doc_i = doc_ids[i]
                real_doc_j = doc_ids[j]
                mag_i = self.index_obj.documents.get(real_doc_i, {}).get('magnitude', 1.0)
                mag_j = self.index_obj.documents.get(real_doc_j, {}).get('magnitude', 1.0)
                
                sim = dot_product / (mag_i * mag_j) if (mag_i * mag_j) > 0 else 0
                matrix[i, j] = matrix[j, i] = round(float(sim), 4)
                
        return matrix

    def search_phrase(self, terms, max_distance=1):
        """REQ-B48: Procura por uma frase exata ou termos próximos usando posições."""
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

        # 3. Verificar proximidade (distância máxima)
        results = []
        for doc_id in common_docs:
            possible_starts = postings_list[0][doc_id]
            
            for start_pos in possible_starts:
                is_match = True
                current_pos = start_pos
                
                for i in range(1, len(terms)):
                    next_term_positions = postings_list[i][doc_id]
                    # O próximo termo tem de estar a uma distância <= max_distance do atual
                    # E à frente do termo anterior (current_pos < pos <= current_pos + max_distance)
                    valid_positions = [pos for pos in next_term_positions if current_pos < pos <= current_pos + max_distance]
                    
                    if not valid_positions:
                        is_match = False
                        break
                    # Atualiza o current_pos para a posição encontrada mais próxima
                    current_pos = valid_positions[0] 
                
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
        # Correção: Se passarem string em vez de lista, separar para não iterar letra a letra
        if isinstance(query_terms, str):
            # Limpar pontuação básica para não falhar no highlight
            raw_terms = [t for t in re.split(r'\W+', query_terms) if t]
            query_terms = [t for t in raw_terms if t.upper() not in {"AND", "OR", "NOT"}]
        doc = self.index_obj.documents.get(doc_id) or self.index_obj.documents.get(str(doc_id))
        if not doc and str(doc_id).isdigit():
            doc = self.index_obj.documents.get(int(doc_id))
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
            base = term[:5] if len(term) > 5 else term
            match = re.search(rf'\b{re.escape(base)}\w*', content, re.IGNORECASE)
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
                base = term[:5] if len(term) > 5 else term
                pattern = rf'(\b{re.escape(base)}\w*)'
                snippet = re.sub(pattern, r'<b>\1</b>', snippet, flags=re.IGNORECASE)
                
            return ("... " if start > 0 else "") + snippet + (" ..." if end < len(content) else "")

        return content[:250] + "..."