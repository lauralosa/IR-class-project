from src.search.indexer import InvertedIndex
from src.search.query_engine import QueryEngine
import json

# 1. Criar um mini-json de teste
mini_data = [
    {"id": 0, "title": "Data Science", "abstract": "Data science is great", "authors": ["Laura"]},
    {"id": 1, "title": "Information Retrieval", "abstract": "Information retrieval is data science", "authors": ["Miguel"]}
]
with open("mini_docs.json", "w") as f:
    json.dump(mini_data, f)

# 2. Inicializar e Indexar
index = InvertedIndex(storage_dir="data/test") # Usa uma pasta de teste limpa
index.index = {} # Garante que o dicionário está vazio
index.create_index("mini_docs.json")

# 3. Testar Query
engine = QueryEngine(index)
results = engine.ranked_search("data science")

print(f"Resultados: {results}")
# Esperado: Doc 0 deve ter score maior que Doc 1 devido ao título e frequência.