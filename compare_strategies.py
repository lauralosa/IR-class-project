import time
from src.search.indexer import InvertedIndex

def run_comparison():
    strategies = ["stemming", "lemmatization"]
    results = {}

    for s in strategies:
        start_time = time.time()
        index = InvertedIndex()
        index.create_index("data/raw_metadata/scraper_results.json", strategy=s)
        duration = time.time() - start_time
        
        results[s] = {
            "time": duration,
            "vocab_size": len(index.index),
            "docs": index.num_docs
        }

    # REQ-B19: Mostrar a comparação ao utilizador
    print("\n--- COMPARAÇÃO DE ESTRATÉGIAS (REQ-B19) ---")
    for s, data in results.items():
        print(f"Estratégia: {s}")
        print(f"  - Tempo de Indexação: {data['time']:.2f}s")
        print(f"  - Tamanho do Vocabulário: {data['vocab_size']} termos")

run_comparison()