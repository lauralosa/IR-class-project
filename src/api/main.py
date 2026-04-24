from fastapi import FastAPI, Query, HTTPException
from src.search.indexer import InvertedIndex
from src.search.query_engine import QueryEngine
from typing import Optional, List

# 1. Inicializar a App
app = FastAPI(
    title="RepositóriUM Search Engine",
    description="API REST para recuperação de informação científica",
    version="1.0.0"
)

# 2. Carregar o Motor (Singleton pattern)
# Ajustamos o caminho conforme a estrutura da tua imagem
json_path = 'src/scraper/scraper_results.json'
indexer = InvertedIndex()
indexer.create_index(json_path)
engine = QueryEngine(indexer)

@app.get("/")
def home():
    return {
        "status": "online",
        "message": "API de Recuperação de Informação pronta.",
        "docs": "/docs"
    }

@app.get("/search")
def search(q: str, method: str = "custom"):
    """
    Pesquisa por Relevância (TF-IDF).
    'method' pode ser 'custom' ou 'sklearn'.
    """
    use_sklearn = (method.lower() == "sklearn")
    results = engine.ranked_search(q, use_sklearn=use_sklearn)
    
    output = []
    for doc_id, score in results:
        doc = indexer.documents[doc_id]
        output.append({
            "id": doc_id,
            "score": round(score, 4),
            "title": doc.get("title"),
            "authors": doc.get("authors"),
            "url": doc.get("pdf_url")
        })
    return {"query": q, "results": output}

@app.get("/boolean")
def boolean_search(q: str, op: str = "AND"):
    """
    Pesquisa Booleana (AND, OR, NOT).
    """
    results_ids = engine.execute_boolean_query(q, operator=op.upper())
    
    output = []
    for doc_id in results_ids:
        doc = indexer.documents[doc_id]
        output.append({
            "id": doc_id,
            "title": doc.get("title"),
            "authors": doc.get("authors"),
            "url": doc.get("pdf_url")
        })
    return {"query": q, "operator": op, "results": output}

# Requisito 3.2.5: Pesquisa por Autor
@app.get("/author/{author_name}")
def search_by_author(author_name: str):
    """
    Filtra documentos por um autor específico.
    """
    results = []
    name_lower = author_name.lower()
    
    for doc_id, doc in indexer.documents.items():
        authors = doc.get("authors", [])
        # Verifica se o nome do autor está na lista de autores do doc
        if any(name_lower in a.lower() for a in authors):
            results.append({
                "id": doc_id,
                "title": doc.get("title"),
                "authors": authors
            })
            
    if not results:
        raise HTTPException(status_code=404, detail="Nenhum documento encontrado para este autor.")
        
    return {"author": author_name, "total": len(results), "results": results}
    