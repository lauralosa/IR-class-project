import time
from src.search.query_engine import QueryEngine
from src.search.indexer import InvertedIndex

def calculate_metrics(retrieved, expected):
    """Calcula Precision, Recall e F1-Score."""
    retrieved_set = set(retrieved)
    expected_set = set(expected)
    
    # Documentos que o motor acertou
    hits = retrieved_set.intersection(expected_set)
    tp = len(hits) # True Positives
    
    precision = tp / len(retrieved_set) if len(retrieved_set) > 0 else 0
    recall = tp / len(expected_set) if len(expected_set) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return precision, recall, f1

def run_evaluation():
    # 1. Preparar o motor
    idx = InvertedIndex()
    if not idx.load_index("index.json"):
        print("Erro: Carrega o índice primeiro!")
        return
    engine = QueryEngine(idx)

    # 2. REQ-B61: O nosso "Gabarito" (Ground Truth) baseado nos teus dados reais
    ground_truth = {
        "cognitive": [1, 2, 8, 11, 15, 16, 21, 23, 25, 26, 31, 66, 75],
        "iot": [2, 3, 6, 7, 8, 10, 11, 12, 13, 15, 16, 17, 21, 23, 26, 27, 33, 68, 108],
        "blockchain": [0, 3, 6, 8, 12, 21, 26, 27, 43, 92]
    }

    # 3. REQ-B62: Comparar dois esquemas (LTC vs NNN)
    schemes = ["ltc", "nnn"]
    
    print("\n" + "="*60)
    print(" RELATÓRIO DE AVALIAÇÃO DE QUALIDADE (REQ-B61/B62)")
    print("="*60)

    for query, expected_ids in ground_truth.items():
        print(f"\n Query: '{query}' (Esperados: {len(expected_ids)} docs)")
        print("-" * 45)
        
        for scheme in schemes:
            # Medir tempo de resposta (REQ-B60)
            start = time.perf_counter()
            results = engine.ranked_search(query, weighting_scheme=scheme)
            end = time.perf_counter()
            
            # Pegamos apenas nos IDs dos resultados
            retrieved_ids = [r[0] for r in results]
            
            # Calcular métricas
            p, r, f1 = calculate_metrics(retrieved_ids, expected_ids)
            
            print(f"Esquema: {scheme.upper()}")
            print(f"  > Precisão: {p:.2%} | Revocação: {r:.2%} | F1-Score: {f1:.4f}")
            print(f"  > Tempo: {(end-start)*1000:.2f}ms")

if __name__ == "__main__":
    run_evaluation()