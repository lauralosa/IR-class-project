import os
from src.search.indexer import InvertedIndex
from src.search.query_engine import QueryEngine

def test_tfidf_ranking():
    # 1. Configuração do Índice
    json_path = 'src/scraper/scraper_results.json'
    if not os.path.exists(json_path):
        json_path = 'scraper_results.json'

    print("--- INICIALIZANDO MOTOR DE BUSCA (MODO RANKING) ---")
    indexer = InvertedIndex()
    indexer.create_index(json_path)
    
    # 2. Inicializar o Query Engine
    engine = QueryEngine(indexer)

    # 3. Queries para testar a relevância
    # Vamos testar termos que aparecem com frequências diferentes
    test_queries = [
        "graphics interaction",
        "algorithm",
        "computational processing of portuguese" 
    ]

    print("\n--- RESULTADOS ORDENADOS POR RELEVÂNCIA (TF-IDF) ---")
    
    for q_str in test_queries:
        # Usamos o novo método ranked_search em vez do booleano
        results = engine.ranked_search(q_str)
        
        print(f"\nQuery: '{q_str}'")
        if results:
            print(f"{'DocID':<7} | {'Score':<10} | {'Título'}")
            print("-" * 60)
            for doc_id, score in results:
                title = indexer.documents[doc_id].get('title', 'N/A')
                # Mostramos apenas os primeiros 50 caracteres do título
                print(f"{doc_id:<7} | {score:<10.4f} | {title[:60]}...")
        else:
            print("  - Nenhum documento encontrado.")

if __name__ == "__main__":
    test_tfidf_ranking()