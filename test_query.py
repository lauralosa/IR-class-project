import os
import numpy as np
from src.search.indexer import InvertedIndex
from src.search.query_engine import QueryEngine

def test_search_engine():
    # 1. Configuração do Caminho (Ajustado para a tua estrutura)
    json_path = 'data/raw_metadata/scraper_results.json'
    if not os.path.exists(json_path):
        json_path = 'src/scraper/scraper_results.json'

    print("---  INICIALIZANDO MOTOR DE BUSCA ---")
    indexer = InvertedIndex()
    # Criamos o índice com stemming por defeito
    indexer.create_index(json_path, strategy="stemming")
    
    engine = QueryEngine(indexer)

    # --- TESTE REQ-B24: MATRIZ DE INCIDÊNCIA ---
    print("\n---  TESTE: MATRIZ DE INCIDÊNCIA (REQ-B24) ---")
    matrix, terms = engine.get_incidence_matrix()
    print(f"Dimensões da Matriz: {matrix.shape} (Termos x Documentos)")
    print(f"Exemplo de termos na matriz: {terms[:5]}")

    # --- TESTE REQ-B23/26: PESQUISAS BOOLEANAS ---
    print("\n---  TESTE: PESQUISAS BOOLEANAS (REQ-B23, B26) ---")
    
    boolean_tests = [
        "graphic interaction",            # REQ-B26: AND Implícito
        "algorithm OR graphics",          # REQ-B23: Operador OR
        "interaction NOT graphics",       # REQ-B23: Operador NOT
        "data AND mining"                 # REQ-B23: Operador AND Explícito
    ]

    for q_str in boolean_tests:
        # Nota: execute_boolean_query agora só recebe a string da query
        results = engine.execute_boolean_query(q_str)
        
        print(f"\nQuery Booleana: '{q_str}'")
        print(f"IDs encontrados: {results[:10]}... (Total: {len(results)})")
        
        if results:
            first_id = results[0]
            title = indexer.documents[first_id].get('title', 'N/A')
            print(f"  -> Exemplo: [{first_id}] {title[:60]}...")

    # --- TESTE REQ-B37: RANKING TF-IDF ---
    print("\n---  TESTE: RANKING TF-IDF / COSSENO (REQ-B37) ---")
    query_rank = "interaction in computer graphics"
    rank_results = engine.ranked_search(query_rank)

    print(f"Query de Ranking: '{query_rank}'")
    for doc_id, score in rank_results[:5]: # Mostrar Top 5
        title = indexer.documents[doc_id].get('title', 'N/A')
        print(f"  - Score: {score:.4f} | [{doc_id}] {title[:60]}...")

if __name__ == "__main__":
    test_search_engine()