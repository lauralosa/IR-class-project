import json
import math
import os
from src.search.processor import TextProcessor

class InvertedIndex:
    def __init__(self):
        self.index = {}      # {termo: [[doc_id, freq], [doc_id, freq], ...]}
        self.skips = {}      
        self.documents = {}  
        self.processor = TextProcessor()
        self.num_docs = 0    # Necessário para o cálculo do IDF

    def create_index(self, json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"Erro: Ficheiro {json_path} não encontrado.")
            return

        self.num_docs = len(data)
        # Definimos onde estão guardados os textos extraídos dos PDFs
        txt_folder = os.path.join("data", "extracted_text")

        for idx, doc in enumerate(data):
            doc_id = idx
            self.documents[doc_id] = doc
            
            # 1. texto básico (Título + Resumo)
            full_text = f"{doc.get('title', '')} {doc.get('abstract', '')}"

            # 2. NOVO: Verificar se este documento tem um ficheiro de texto integral
            # O PDFHandler guarda como doc_0.txt, doc_1.txt, etc.
            txt_filename = f"doc_{idx}.txt"
            txt_path = os.path.join(txt_folder, txt_filename)

            if os.path.exists(txt_path):
                try:
                    with open(txt_path, 'r', encoding='utf-8') as f_txt:
                        # Lemos o conteúdo do PDF e juntamos ao título/abstract
                        pdf_content = f_txt.read()
                        full_text += " " + pdf_content
                except Exception as e:
                    print(f"Aviso: Não foi possível ler o texto integral de {txt_filename}: {e}")
            
            # 3. Agora processamos o texto todo (Metadados + PDF)
            tokens = self.processor.process_text(full_text, use_stemming=True)
            
            term_frequencies = {}
            for token in tokens:
                term_frequencies[token] = term_frequencies.get(token, 0) + 1
            
            for token, count in term_frequencies.items():
                if token not in self.index:
                    self.index[token] = []
                # Guardamos doc_id e a frequência (TF)
                self.index[token].append([doc_id, count])
        
        # Ordenamos por doc_id (o primeiro elemento do sub-par [id, freq])
        for term in self.index:
            self.index[term].sort(key=lambda x: x[0])

        self._add_skip_pointers()
        print(f"Índice criado: {len(self.index)} termos, {self.num_docs} documentos.")

    def get_postings(self, term):
        """Retorna os postings [doc_id, freq] e os skips para um termo."""
        return self.index.get(term, []), self.skips.get(term, [])
        
    def get_idf(self, term):
        """Calcula o Inverse Document Frequency (Requisito 3.2.5)."""
        df = len(self.index.get(term, []))
        if df == 0:
            return 0
        # Fórmula: log10(N / df)
        return math.log10(self.num_docs / df)

    def _add_skip_pointers(self):
        for term, postings in self.index.items():
            L = len(postings)
            skip_interval = round(math.sqrt(L))
            if L > 2 and skip_interval > 1:
                self.skips[term] = [i for i in range(0, L, skip_interval)]
            else:
                self.skips[term] = []

    def save_index(self, path='index.json'):
        data_to_save = {
            'index': self.index,
            'skips': self.skips,
            'documents': self.documents,
            'num_docs': self.num_docs
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=4)