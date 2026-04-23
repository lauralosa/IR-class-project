import json
import math
from src.search.processor import TextProcessor

class InvertedIndex:
    def __init__(self):
        self.index = {}      # {termo: [id1, id2, id3, ...]}
        self.skips = {}      # {termo: [índices_com_salto]}
        self.documents = {}  # {id: {title, abstract, ...}}
        self.processor = TextProcessor()

    def create_index(self, json_path):
        """
        Lê o JSON do scraper, constrói o índice e gera os Skip Pointers.
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"Erro: Ficheiro {json_path} não encontrado.")
            return

        # 1. Construção do Índice Base
        for idx, doc in enumerate(data):
            doc_id = idx
            self.documents[doc_id] = doc
            
            # Indexamos título e abstract
            full_text = f"{doc.get('title', '')} {doc.get('abstract', '')}"
            tokens = self.processor.process_text(full_text, use_stemming=True)
            
            for token in set(tokens): # set() para evitar duplicados no mesmo doc
                if token not in self.index:
                    self.index[token] = []
                self.index[token].append(doc_id)
        
        # Ordenar as listas de postings (essencial para Skip Pointers e Boolean Search)
        for term in self.index:
            self.index[term].sort()

        # 2. Gerar Skip Pointers (Requisito 3.2.3)
        self._add_skip_pointers()

        print(f"Índice criado: {len(self.index)} termos, {len(self.documents)} documentos.")

    def _add_skip_pointers(self):
        """
        Adiciona atalhos matemáticos para acelerar pesquisas AND.
        Frequência de salto: raiz quadrada do tamanho da lista (√L).
        """
        for term, postings in self.index.items():
            L = len(postings)
            skip_interval = round(math.sqrt(L))
            
            # Só faz sentido criar skips em listas com mais de 2 elementos
            if L > 2 and skip_interval > 1:
                # Guardamos as posições (índices) na lista de postings que têm salto
                self.skips[term] = [i for i in range(0, L, skip_interval)]
            else:
                self.skips[term] = []

    def save_index(self, path='index.json'):
        """Persistência do índice (requisito de sistema)."""
        data_to_save = {
            'index': self.index,
            'skips': self.skips,
            'documents': self.documents
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=4)
            print(f"Sucesso: Índice e Skips guardados em {path}")

    def get_postings(self, term):
        """Retorna a lista de IDs e os skips para um termo."""
        return self.index.get(term, []), self.skips.get(term, [])