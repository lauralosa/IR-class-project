from src.search.indexer import InvertedIndex
from src.search.query_engine import QueryEngine

idx = InvertedIndex()
idx.load_index()
engine = QueryEngine(idx)

# Teste REQ-B39: Esquemas diferentes
print("\n---  TESTE REQ-B39: Esquemas de Pesagem ---")
q = "artificial intelligence"
print(f"TF-IDF: {engine.ranked_search(q, weighting_scheme='tfidf')[:2]}")
print(f"BINARY: {engine.ranked_search(q, weighting_scheme='binary')[:2]}")

# Teste REQ-B40: Matriz de Similaridade
print("\n---  TESTE REQ-B40: Matriz de Similaridade Doc-Doc ---")
sim_matrix = engine.get_document_similarity_matrix()
print(f"Dimensões da Matriz: {sim_matrix.shape}")
print("Similaridade entre Doc 0 e Doc 1:", sim_matrix[0, 1])