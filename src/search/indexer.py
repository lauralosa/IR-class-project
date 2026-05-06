import json
import math
import os
from datetime import datetime
from typing import List  # NOVO: Necessário para as type hints
from src.search.processor import TextProcessor

class InvertedIndex:
    def __init__(self, storage_dir="data"):
        self.index = {}      
        self.skips = {}      
        self.documents = {}  
        self.processor = TextProcessor()
        self.num_docs = 0    
        self.author_index = {}
        self.storage_dir = storage_dir 
        self.doc_magnitudes = {}
        self.metadata = {
            'reduction_strategy': None,
            'indexed_at': None,
            'vocab_size': 0
        }

    def _clean_full_text(self, text):
        """Heurística para remover bibliografia e índices."""
        markers = ["referências", "references", "bibliografia", "bibliography"]
        temp_text = text.lower()
        
        for marker in markers:
            if marker in temp_text:
                # Encontra a última ocorrência do marcador para evitar cortes precoces
                idx = temp_text.rfind(marker)
                # Corta o texto, mantendo apenas o que está antes da bibliografia
                return text[:idx]
        return text

    def create_index(self, json_path,strategy = "stemming",remove_stopwords=True):
        # 1. Limpar sempre o índice antes de começar (Garante o isolamento do teste)
        self.index = {}
        self.documents = {}
        self.metadata['reduction_strategy'] = strategy
        self.metadata['stop_words_removed'] = remove_stopwords

        """Lê os metadados e o texto integral para construir o índice."""
        # REQ-B10: Garantir que a pasta de armazenamento existe
        processed_dir = os.path.join("data", "processed_text")
        os.makedirs(processed_dir, exist_ok=True) # Cria a pasta se não existir

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"Erro: Ficheiro {json_path} não encontrado.")
            return

        self.num_docs = len(data)
        txt_folder = os.path.join("data", "extracted_text")
        self._build_author_index(data)

        

        for idx, doc in enumerate(data):
            doc_id = idx
            self.documents[doc_id] = doc
            
            # Texto básico
            full_text = f"{doc.get('title', '')} {doc.get('abstract', '')}"

            # REQ-B10: Integrar texto integral do PDF
            txt_filename = f"doc_{idx}.txt"
            txt_path = os.path.join(txt_folder, txt_filename)



            if os.path.exists(txt_path):
                try:
                    with open(txt_path, 'r', encoding='utf-8') as f_txt:
                        raw_pdf_text = f_txt.read()
                        cleaned_pdf_text = self._clean_full_text(raw_pdf_text) 
                        full_text += " " + cleaned_pdf_text


                except Exception as e:
                    print(f"Aviso: Erro ao ler {txt_filename}: {e}")
            
            # Processamento NLTK (REQ-B13)
            if strategy == "lemmatization":
                # REQ-B17: Usa Lematização via WordNet
                tokens = self.processor.process_text(full_text, use_stemming=False, use_lemmatization=True, remove_stopwords=True)
            else:
                # REQ-B16: Usa Stemming de Porter (Default)
                tokens = self.processor.process_text(full_text, use_stemming=True, use_lemmatization=False, remove_stopwords=True)

            # --- Persistência ---
            processed_path = os.path.join(processed_dir, f"doc_{doc_id}.json")
            with open(processed_path, 'w', encoding='utf-8') as f_out:
                json.dump(tokens, f_out) # Guardamos os tokens/stems no disco
            
            # Atualizamos o documento com o caminho da versão processada
            doc['processed_text_path'] = processed_path
            self.documents[doc_id] = doc
            # ------------------------------------------
            
            # Cálculo de Term Frequency (TF) local (REQ-B32)
            term_frequencies = {}
            for token in tokens:
                term_frequencies[token] = term_frequencies.get(token, 0) + 1
            
            for token, count in term_frequencies.items():
                if token not in self.index:
                    self.index[token] = []
                self.index[token].append([doc_id, count])
        
        # Ordenar postings por doc_id para permitir Skip Pointers (REQ-B29)
        for term in self.index:
            self.index[term].sort(key=lambda x: x[0])

        self._add_skip_pointers()
        self._calculate_doc_magnitudes()
        self.save_index()
        print(f"Índice criado: {len(self.index)} termos, {self.num_docs} documentos.")

    def _calculate_doc_magnitudes(self):
        """Calcula a norma L2 para cada documento (REQ-B37)."""
        # Dicionário temporário para acumular a soma dos quadrados: sum(w^2)
        sums_of_squares = {doc_id: 0.0 for doc_id in self.documents.keys()}

        for term, postings in self.index.items():
            idf = self.get_idf(term) # Usa a tua função de IDF com suavização
            
            for doc_id, tf in postings:
                # Peso w = tf * idf (conforme REQ-B34)
                weight = tf * idf
                sums_of_squares[doc_id] += weight ** 2

        # A magnitude final é a raiz quadrada da soma
        import math
        for doc_id, total_sum in sums_of_squares.items():
            self.doc_magnitudes[doc_id] = math.sqrt(total_sum)
    
    

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

    def save_index(self, filename='index.json'):
        """
        Guarda a estrutura completa seguindo o REQ-B12 e REQ-B30 (TF e DF).
        """
        # 1. Garantir que o caminho usa o storage_dir definido no projeto
        path = os.path.join(self.storage_dir, filename)
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
            'vocabulary': vocabulary_data # O índice propriamente dito
            
        }
        
        # 5. Gravar no disco (usando o 'path' completo)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=4, ensure_ascii=False)
        
        print(f" Índice estruturado com sucesso em: {path}")

    def load_index(self, filename="index.json"):
        """
        Carrega o índice estruturado para memória.
        """
        if not os.path.exists(filename):
            print(" Ficheiro de índice não encontrado.")
            return False

        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.num_docs = data["metadata"]["total_docs"]
        self.documents = {int(k): v for k, v in data["documents"].items()}
        
        # Reconstruir o índice interno
        self.index = {}
        for term, content in data["vocabulary"].items():
            self.index[term] = content["postings"]
        
        # Restaurar metadados
        self.metadata['reduction_strategy'] = data["metadata"].get("reduction_strategy", "stemming")
        self.metadata['stop_words_removed'] = data["metadata"]["stop_words_removed"]
        
        print(f" Índice carregado: {self.num_docs} documentos.")
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
            
            self.documents[next_id] = doc
            text = f"{doc.get('title', '')} {doc.get('abstract', '')}"
            
            # 1. Atenção aos parâmetros: usa a estratégia guardada nos metadados
            strategy = self.metadata.get('reduction_strategy', 'stemming')
            tokens = self.processor.process_text(
                text, 
                use_stemming=(strategy == 'stemming'),
                use_lemmatization=(strategy == 'lemmatization')
            )
            
            term_freqs = {}
            for token in tokens:
                term_freqs[token] = term_freqs.get(token, 0) + 1
                
            for term, tf in term_freqs.items():
                if term not in self.index:
                    self.index[term] = []
                self.index[term].append([next_id, tf])
            
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