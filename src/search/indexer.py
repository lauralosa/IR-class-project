import json
import math
import os
from datetime import datetime
from typing import List  # NOVO: Necessário para as type hints
from src.search.processor import TextProcessor
import time
import psutil
import logging
from src.config import settings
from src.ml.classifier import DocumentClassifier

# Configuração do Logger (REQ-B69)
logger = logging.getLogger("INDEXER")

class InvertedIndex:
    def __init__(self):
        self.index = {}      
        self.skips = {}      
        self.documents = {}  
        self.processor = TextProcessor()
        self.classifier = DocumentClassifier() # Integrou o modelo de ML
        self.num_docs = 0    
        self.author_index = {}
        self.doc_magnitudes = {}
        self.metadata = {
            'reduction_strategy': 'stemming',
            'indexed_at': None,
            'vocab_size': 0,
            'stop_words_removed': True
        }

        # REQ-B67: Centralizar pastas usando settings
        self.storage_dir = settings.STORAGE_DIR
        os.makedirs(self.storage_dir, exist_ok=True)

    def _clean_full_text(self, text):
        """Heurística para remover bibliografia e índices, restrita ao final do documento."""
        markers = ["referências", "references", "bibliografia", "bibliography"]
        temp_text = text.lower()
        
        # Procuramos os marcadores apenas nos últimos 30% do documento
        # para evitar cortes se a palavra for usada no abstract.
        search_start = int(len(temp_text) * 0.70)
        
        for marker in markers:
            idx = temp_text.find(marker, search_start)
            if idx != -1:
                return text[:idx]
        return text

    def create_index(self, json_path=None, strategy="stemming", remove_stopwords=True, batch_size=None):
        
        # --- Alteração: Uso de caminhos dinâmicos do settings ---
        target_path = json_path or settings.RAW_DATA_PATH
        b_size = batch_size or settings.DEFAULT_BATCH_SIZE

        # --- [INÍCIO B56 & B58] MONITORIZAÇÃO ---
        process = psutil.Process(os.getpid())
        mem_antes = process.memory_info().rss / (1024 * 1024) # MB
        tempo_inicio = time.perf_counter()
        # ---------------------------------------

        # 1. Limpar sempre o índice antes de começar (Garante o isolamento do teste)
        self.index = {}
        self.documents = {}
        self.metadata['reduction_strategy'] = strategy
        self.metadata['stop_words_removed'] = remove_stopwords

        """Lê os metadados e o texto integral para construir o índice."""
        # REQ-B10: Garantir que a pasta de armazenamento existe
        processed_dir = os.path.join(self.storage_dir, "processed_text")
        os.makedirs(processed_dir, exist_ok=True) # Cria a pasta se não existir

        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"Erro: Ficheiro {json_path} não encontrado.")
            return

        self.num_docs = len(data)
        txt_folder = settings.TXT_STORAGE_PATH
        self._build_author_index(data)

        # REQ-B42: Treinar classificador ML antes da indexação
        docs_dict = {i: d for i, d in enumerate(data)}
        self.classifier.prepare_and_train(docs_dict)

        logger.info(f"A processar {self.num_docs} documentos em lotes de {b_size}...")

        for i in range(0, self.num_docs, b_size):
            lote = data[i : i + b_size]

            for sub_idx, doc in enumerate(lote):
                doc_id = i + sub_idx
                self.documents[doc_id] = doc
                
                # Texto básico
                full_text = f"{doc.get('title', '')} {doc.get('abstract', '')}"

                # REQ-B10: Integrar texto integral do PDF
                txt_filename = f"doc_{doc_id}.txt"
                txt_path = os.path.join(txt_folder, txt_filename)



                if os.path.exists(txt_path):
                    try:
                        with open(txt_path, 'r', encoding='utf-8') as f_txt:
                            raw_pdf_text = f_txt.read()
                            cleaned_pdf_text = self._clean_full_text(raw_pdf_text) 
                            full_text += " " + cleaned_pdf_text


                    except Exception as e:
                        print(f"Aviso: Erro ao ler {txt_filename}: {e}")
                
                # Processamento NLP
                tokens = self.processor.process_text(
                    full_text, 
                    use_stemming=(strategy == "stemming"), 
                    use_lemmatization=(strategy == "lemmatization"), 
                    remove_stopwords=remove_stopwords
                )

                # REQ-B43: Categorização Automática
                doc['category'] = self.classifier.predict_category(doc.get('title', ''), doc.get('abstract', ''))

                # --- Persistência ---
                processed_path = os.path.join(processed_dir, f"doc_{doc_id}.json")
                with open(processed_path, 'w', encoding='utf-8') as f_out:
                    json.dump(tokens, f_out) # Guardamos os tokens/stems no disco
                
                # Atualizamos o documento com o caminho da versão processada
                doc['processed_text_path'] = processed_path
                self.documents[doc_id] = doc
                # ------------------------------------------
                
                # REQ-B48: Guardar posições para permitir Phrase Queries
                term_data = {} # Vamos guardar as posições de cada token
                for pos, token in enumerate(tokens):
                    if token not in term_data:
                        term_data[token] = []
                    term_data[token].append(pos)

                for token, positions in term_data.items():
                    if token not in self.index:
                        self.index[token] = []
                    # Agora guardamos a lista de posições em vez de um número fixo
                    self.index[token].append([doc_id, positions])

            logger.info(f"Lote concluído: {min(i + b_size, self.num_docs)}/{self.num_docs}")
        
        # Ordenar postings por doc_id para permitir Skip Pointers (REQ-B29)
        for term in self.index:
            self.index[term].sort(key=lambda x: x[0])

        self._add_skip_pointers()
        self._calculate_doc_magnitudes()
        self.save_index()
        # --- [FIM B56 & B58] CÁLCULO DE MÉTRICAS ---
        tempo_fim = time.perf_counter()
        mem_depois = process.memory_info().rss / (1024 * 1024) # MB
        
        tempo_total = tempo_fim - tempo_inicio
        mem_consumida = mem_depois - mem_antes

        # Guardar nos metadados para o REQ-B12
        self.metadata['performance'] = {
            'indexing_time_sec': round(tempo_total, 4),
            'memory_usage_mb': round(mem_consumida, 2)
        }
        logger.info(f"Indexação concluída: {tempo_total:.2f}s | Vocabulário: {len(self.index)} termos.")


    def _calculate_doc_magnitudes(self):
        """Calcula a norma L2 para cada documento (REQ-B37)."""
        # Dicionário temporário para acumular a soma dos quadrados: sum(w^2)
        sums_of_squares = {doc_id: 0.0 for doc_id in self.documents.keys()}

        for term, postings in self.index.items():
            idf = self.get_idf(term) # Usa a tua função de IDF com suavização
            
            for posting in postings:
                doc_id = posting[0]
                positions = posting[1] # Lista de posições
                tf = len(positions)
                # Peso w = tf * idf (conforme REQ-B34)
                weight = tf * idf
                sums_of_squares[doc_id] += weight ** 2

        # A magnitude final é a raiz quadrada da soma
        
        # 3. Calcular a raiz quadrada e GUARDAR no sítio certo
        for doc_id, total_sum in sums_of_squares.items():
            magnitude = math.sqrt(total_sum)
            
            # CRÍTICO: Guardar dentro do dicionário documents para o QueryEngine ler!
            if doc_id in self.documents:
                self.documents[doc_id]['magnitude'] = magnitude
            
            # Também mantemos no doc_magnitudes se precisares para outros métodos
            self.doc_magnitudes[doc_id] = magnitude
    
    

    def _build_author_index(self, publications: List[dict]):
        """Cria a relação Autor -> Documentos (REQ-B11)."""
        for idx, pub in enumerate(publications):
            authors = pub.get('authors', [])
            for author in authors:
                if author not in self.author_index:
                    self.author_index[author] = []
                # Usamos o idx como doc_id para consistência
                if idx not in self.author_index[author]:
                    self.author_index[author].append(idx)
        
        # Guardar índice de autores (REQ-B09)
        author_path = os.path.join(self.storage_dir, "author_index.json")
        with open(author_path, "w", encoding="utf-8") as f:
            json.dump(self.author_index, f, ensure_ascii=False, indent=4)

    def get_postings(self, term):
        """
        Retorna a lista de postings [doc_id, freq] e os skips para um termo.
        Este método é obrigatório para o QueryEngine funcionar.
        """
        return self.index.get(term, []), self.skips.get(term, [])

    def get_idf(self, term):
        """Calcula o IDF com suavização para evitar zeros em coleções pequenas (REQ-B33)."""
        df = len(self.index.get(term, []))
        if df == 0:
            return 0
        # Usamos log10(N / df) + 1 para garantir que o peso nunca seja totalmente zero
        return math.log10(self.num_docs / df) + 1

    def _add_skip_pointers(self):
            """Implementa saltos lógicos nas listas de postings (REQ-B29)."""
            for term, postings in self.index.items():
                L = len(postings)
                skip_interval = round(math.sqrt(L))
                if L > 2 and skip_interval > 1:
                    self.skips[term] = [i for i in range(0, L, skip_interval)]
                else:
                    self.skips[term] = []

    def save_index(self, filename=None):
        """
        Guarda a estrutura completa seguindo o REQ-B12 e REQ-B30 (TF e DF).
        """
        # 1. Garantir que o caminho usa o storage_dir definido no projeto
        path = filename or settings.INDEX_FILE
        # 2. Estruturar o vocabulário para incluir o DF (REQ-B30)
        # Transformamos o índice simples numa estrutura rica
        vocabulary_data = {}
        for term, postings in self.index.items():
            vocabulary_data[term] = {
                "df": len(postings),      # Document Frequency: total de docs com o termo
                "postings": postings     # Listas de [doc_id, tf] (REQ-B28)
            }

        # 3. Atualizar metadados finais
        self.metadata['total_docs'] = self.num_docs
        self.metadata['vocab_size'] = len(self.index)
        self.metadata['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 4. Organizar o dicionário final para o JSON
        data_to_save = {
            'metadata': self.metadata, 
            'documents': self.documents, # Metadados dos documentos (títulos, magnitudes, etc)
            'vocabulary': vocabulary_data, # O índice propriamente dito
            'skips': self.skips
            
        }
        
        # 5. Gravar no disco (usando o 'path' completo)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=4, ensure_ascii=False)
        
        print(f" Índice estruturado com sucesso em: {path}")

    def load_index(self, filename=None):
        
        """
        Carrega o índice estruturado para memória.
        """
        path = filename or settings.INDEX_FILE

        if not os.path.exists(path):
            logger.warning("Ficheiro de índice não encontrado.")
            return False

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.num_docs = data["metadata"]["total_docs"]
        self.documents = {k: v for k, v in data["documents"].items()}
        
        # Reconstruir o índice interno
        self.index = {}
        for term, content in data["vocabulary"].items():
            self.index[term] = content["postings"]
        
        # Restaurar metadados
        self.metadata['reduction_strategy'] = data["metadata"].get("reduction_strategy", "stemming")
        self.metadata['stop_words_removed'] = data["metadata"]["stop_words_removed"]
        
        # Treinar o classificador com os dados carregados
        self.classifier.prepare_and_train(self.documents)
        
        logger.info(f"Índice carregado ({self.metadata['reduction_strategy']}).")
        return True

    def update_index(self, new_json_path):
        """REQ-B31: Adiciona novos documentos ao índice de forma robusta."""
        if not self.documents:
            self.load_index()

        with open(new_json_path, 'r', encoding='utf-8') as f:
            new_data = json.load(f)

        next_id = max(self.documents.keys()) + 1 if self.documents else 0
        docs_added = 0 # Contador para sabermos se vale a pena gravar no fim

        for doc in new_data:
            if any(d['title'] == doc['title'] for d in self.documents.values()):
                continue
            
            # REQ-B43: Classificar novo documento
            doc['category'] = self.classifier.predict_category(doc.get('title', ''), doc.get('abstract', ''))
            self.documents[next_id] = doc
            text = f"{doc.get('title', '')} {doc.get('abstract', '')} {doc.get('category', '')}"
            
            # 1. Atenção aos parâmetros: usa a estratégia guardada nos metadados
            strategy = self.metadata.get('reduction_strategy', 'stemming')
            tokens = self.processor.process_text(
                text, 
                use_stemming=(strategy == 'stemming'),
                use_lemmatization=(strategy == 'lemmatization')
            )
            
            # --- Correção: Persistir tokenização do documento ---
            processed_dir = os.path.join(self.storage_dir, "processed_text")
            os.makedirs(processed_dir, exist_ok=True)
            processed_path = os.path.join(processed_dir, f"doc_{next_id}.json")
            with open(processed_path, 'w', encoding='utf-8') as f_out:
                json.dump(tokens, f_out)
            self.documents[next_id]['processed_text_path'] = processed_path

            # --- Correção: Atualizar índice de autores ---
            authors = doc.get('authors', [])
            for author in authors:
                if author not in self.author_index:
                    self.author_index[author] = []
                if next_id not in self.author_index[author]:
                    self.author_index[author].append(next_id)
            
            # --- Correção: Estrutura [doc_id, positions] em vez de [doc_id, tf] ---
            term_positions = {}
            for pos, token in enumerate(tokens):
                if token not in term_positions:
                    term_positions[token] = []
                term_positions[token].append(pos)
                
            for term, positions in term_positions.items():
                if term not in self.index:
                    self.index[term] = []
                self.index[term].append([next_id, positions])
            
            next_id += 1
            docs_added += 1

        
        if docs_added > 0:
            # A. Atualizar o contador global
            self.num_docs = len(self.documents)
            
            # B. Recalcular Magnitudes (REQ-B37)
            # Sem isto, o score dos novos documentos será zero ou da erro
            self._calculate_doc_magnitudes() 
            
            # C. Persistir no disco (REQ-B12)
            self.save_index()
            
            print(f"Sucesso: {docs_added} novos documentos indexados. Total: {self.num_docs}")
        else:
            print("ℹ️ Nenhum documento novo para adicionar.")