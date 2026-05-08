import os
from src.search.indexer import InvertedIndex
from src.search.query_engine import QueryEngine

def compare_engines():
    # 1. Configuração do caminho do scraper (ajustado para a tua estrutura)
    json_path = 'data/raw_metadata/scraper_results.json'
    if not os.path.exists(json_path):
        json_path = 'scraper_results.json'

    indexer = InvertedIndex()
    
    # 2. Criar ou Carregar o Índice
    # Para garantir que os metadados estão frescos, vamos criar
    print("---  A PROCESSAR ÍNDICE ---")
    indexer.create_index(json_path)
    engine = QueryEngine(indexer)

    query = "computational processing of portuguese"
    
    print(f"\n QUERY DE TESTE: '{query}'")
    print("="*50)
    
    # --- [CUSTOM TF-IDF - REQ-B34] ---
    print("\n---  [CUSTOM TF-IDF IMPLEMENTATION] ---")
    custom_results = engine.ranked_search(query, use_sklearn=False)
    
    if not custom_results:
        print("Nenhum resultado encontrado no modelo Custom.")
    else:
        for doc_id, score in custom_results[:3]:
            title = indexer.documents[doc_id].get('title', 'N/A')
            print(f"Score: {score:.4f} | ID: {doc_id} | Título: {title[:60]}...")

    # --- [SKLEARN + COSINE - REQ-B35] ---
    print("\n---  [SKLEARN TF-IDF + COSINE SIMILARITY] ---")
    sklearn_results = engine.ranked_search(query, use_sklearn=True)
    
    if not sklearn_results:
        print("Nenhum resultado encontrado no modelo Sklearn.")
    else:
        for doc_id, score in sklearn_results[:3]:
            title = indexer.documents[doc_id].get('title', 'N/A')
            print(f"Score: {score:.4f} | ID: {doc_id} | Título: {title[:60]}...")



if __name__ == "__main__":
    compare_engines()