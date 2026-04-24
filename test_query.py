import os
from src.search.indexer import InvertedIndex
from src.search.query_engine import QueryEngine

def test_search_engine():
    # 1. Configuração do Índice
    json_path = 'src/scraper/scraper_results.json'
    if not os.path.exists(json_path):
        json_path = 'scraper_results.json'

    print("--- INICIALIZANDO MOTOR DE BUSCA ---")
    indexer = InvertedIndex()
    indexer.create_index(json_path)
    
    # 2. Inicializar o Query Engine
    engine = QueryEngine(indexer)

    # 3. Lista de Testes (Query, Operador)
    tests = [
        ("graphic interaction", "AND"),  # Deve aparecer no doc 0
        ("algorithm graphics", "OR"),    # Deve aparecer em vários
        ("graphic interaction", "NOT")         # Ex: Termo1="graphic", Termo2="interaction" -> Docs com algoritm mas sem graphics
    ]

    print("\n--- EXECUTANDO PESQUISAS BOOLEANAS ---")
    
    for q_str, op in tests:
        results = engine.execute_boolean_query(q_str, operator=op)
        
        print(f"\nQuery: '{q_str}' | Operador: {op}")
        print(f"IDs encontrados: {results}")
        
        # Mostrar os títulos para validar
        if results:
            print("Títulos encontrados:")
            for doc_id in results:
                title = indexer.documents[doc_id].get('title', 'N/A')
                print(f"  - [{doc_id}] {title}")
        else:
            print("  - Nenhum documento encontrado.")

if __name__ == "__main__":
    test_search_engine()