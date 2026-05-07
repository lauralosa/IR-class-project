import os
import numpy as np
from src.search.indexer import InvertedIndex
from src.search.query_engine import QueryEngine

def test_search_engine():
    # 1. Configuração do Caminho
    json_path = 'data/raw_metadata/scraper_results.json'
    if not os.path.exists(json_path):
        json_path = 'src/scraper/scraper_results.json'

    print("---  INICIALIZANDO MOTOR DE BUSCA ---")
    indexer = InvertedIndex()
    # Carregamos o índice (ou criamos se for a primeira vez)
    indexer.load_index() 
    
    engine = QueryEngine(indexer)

    # --- TESTE REQ-B24: MATRIZ DE INCIDÊNCIA ---
    print("\n---  TESTE: MATRIZ DE INCIDÊNCIA (REQ-B24) ---")
    matrix, terms = engine.get_incidence_matrix()
    print(f"Dimensões da Matriz: {matrix.shape} (Termos x Documentos)")
    print(f"Exemplo de termos: {terms[:5]}")

    # --- TESTE REQ-B45/48: BOOLEANAS COMPLEXAS E FRASES ---
    print("\n---  TESTE: BOOLEANAS COMPLEXAS E FRASES (REQ-B45, B48) ---")
    
    complex_tests = [
        '"human aware assistance"',                 # REQ-B48: Frase Exata
        '"cognitive vehicles" AND NOT "human aware"', # REQ-B45/48: Frase + Precedência
        "algorithm OR graphics",                     # REQ-B23: Operador OR
        "interaction NOT graphics",                  # REQ-B23: Operador NOT
    ]

    for q_str in complex_tests:
        results = engine.execute_boolean_query(q_str)
        print(f"\nQuery: '{q_str}'")
        print(f"IDs encontrados: {results[:10]} (Total: {len(results)})")
        
        if results:
            first_id = results[0]
            doc_data = indexer.documents.get(first_id) or indexer.documents.get(str(first_id))
            title = doc_data.get('title', 'N/A') if doc_data else 'Documento não encontrado'
            print(f"  -> Top Result: [{first_id}] {title[:60]}...")
            

    # --- TESTE REQ-B47: EXPANSÃO DE QUERY ---
    print("\n---  TESTE: EXPANSÃO DE QUERY (REQ-B47) ---")
    query_exp = "vehicle"
    # Sem expansão
    res_normal = engine.execute_boolean_query(query_exp, expand=False)
    # Com expansão (busca sinónimos como 'automobile', 'car', etc.)
    res_expanded = engine.execute_boolean_query(query_exp, expand=True)
    
    print(f"Query: '{query_exp}'")
    print(f"Resultados Normais: {len(res_normal)}")
    print(f"Resultados Expandidos: {len(res_expanded)}")
    print(f"Diferença (Recall): +{len(res_expanded) - len(res_normal)} documentos")

    # --- TESTE REQ-B37: RANKING TF-IDF ---
    print("\n---  TESTE: RANKING TF-IDF / COSSENO (REQ-B37) ---")
    query_rank = "interaction in computer graphics"
    rank_results = engine.ranked_search(query_rank)

    print(f"Query de Ranking: '{query_rank}'")
    for doc_id, score in rank_results[:5]:
        doc_data = indexer.documents.get(first_id) or indexer.documents.get(str(first_id))
        title = doc_data.get('title', 'N/A') if doc_data else 'Documento não encontrado'
        print(f"  - Score: {score:.4f} | [{doc_id}] {title[:60]}...")

if __name__ == "__main__":
    test_search_engine()