from src.search.indexer import InvertedIndex
import os

def test_indexing():
    # 1. Caminho para os dados do scraper
    # Ajusta se o teu ficheiro estiver na raiz ou dentro de src/scraper/
    json_path = 'data/raw_metadata/scraper_results.json'
    
    if not os.path.exists(json_path):
        # Tenta na raiz se não encontrar na pasta do scraper
        json_path = 'scraper_results.json'

    print(f"--- TESTE DO ÍNDICE INVERTIDO ---")
    
    # 2. Inicializar o Indexante
    idx = InvertedIndex()
    
    # 3. Criar o Índice
    idx.create_index(json_path, strategy="lemmatization", batch_size=50)
    
    # 4. Verificar alguns termos
    # Vamos testar termos que sabemos que existem nos teus 15 docs
    test_terms = ['graphic', 'interact', 'comput', 'data', 'algorithm']
    
    print("\nResultados da Pesquisa no Índice (Postings):")
    for term in test_terms:
        postings = idx.get_postings(term)
        print(f"Palavra '{term}': encontrada nos documentos {postings}")

    # 5. Guardar o índice para ver o ficheiro JSON final
    idx.save_index('index.json')
    print("\n[OK] Índice guardado em 'index.json' para inspeção visual.")

if __name__ == "__main__":
    test_indexing()
    