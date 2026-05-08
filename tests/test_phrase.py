from src.search.query_engine import QueryEngine
from src.search.indexer import InvertedIndex

idx = InvertedIndex()
idx.load_index()
engine = QueryEngine(idx)

# No teu ficheiro de teste:
query_bruta = "human aware assistance"
# IMPORTANTE: Passar pelo mesmo processador do índice!
termos_processados = engine.processor.process_text(query_bruta, use_stemming=True)

print(f"Termos que vamos procurar: {termos_processados}")

docs = engine.search_phrase(termos_processados)
print(f"🔎 Resultados: {docs}")