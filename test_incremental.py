from src.search.indexer import InvertedIndex
from src.search.query_engine import QueryEngine
import os

def run_incremental_test():
    indexer = InvertedIndex()
    
    # 1. Carregar o índice atual (os 110 docs)
    print("---  PASSO 1: Carregar índice existente ---")
    if not indexer.load_index():
        print("Erro: Precisas de ter um 'index.json' já criado. Corre o indexador primeiro!")
        return
    
    docs_antes = indexer.num_docs
    print(f"Documentos no índice antes: {docs_antes}")

    # 2. Correr a atualização incremental
    print("\n---  PASSO 2: Atualizar com novos documentos ---")
    indexer.update_index('new_docs.json')

    # 3. Validar resultados
    print("\n---  PASSO 3: Validação Técnica ---")
    docs_depois = indexer.num_docs
    print(f"Documentos no índice depois: {docs_depois}")

    if docs_depois > docs_antes:
        print(" SUCESSO: O contador de documentos aumentou!")
    
    # 4. Testar se o novo documento é pesquisável
    engine = QueryEngine(indexer)
    print("\n---  PASSO 4: Teste de Pesquisa ---")
    query = "Braga AND inteligência"
    results = engine.execute_boolean_query(query)
    
    print(f"Pesquisa por '{query}':")
    if results:
        for doc_id in results:
            title = indexer.documents[doc_id]['title']
            print(f"  -> Encontrado no ID {doc_id}: {title}")
    else:
        print("  ->  Erro: O novo documento não foi encontrado na pesquisa.")

if __name__ == "__main__":
    run_incremental_test()