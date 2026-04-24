from src.search.indexer import InvertedIndex
from src.search.query_engine import QueryEngine

def compare_engines():
    indexer = InvertedIndex()
    indexer.create_index('src/scraper/scraper_results.json')
    engine = QueryEngine(indexer)

    query = "computational processing of portuguese"
    
    print(f"\nQUERY: {query}")
    
    print("\n--- [CUSTOM TF-IDF] ---")
    for doc_id, score in engine.ranked_search(query, use_sklearn=False)[:3]:
        print(f"ID: {doc_id} | Score: {score:.4f}")

    print("\n--- [SKLEARN + COSINE] ---")
    for doc_id, score in engine.ranked_search(query, use_sklearn=True)[:3]:
        print(f"ID: {doc_id} | Score: {score:.4f}")

if __name__ == "__main__":
    compare_engines()