from fastapi import FastAPI, Query, HTTPException, Response
from src.search.indexer import InvertedIndex
from src.search.query_engine import QueryEngine
from typing import Optional, List
import dicttoxml

# 1. Inicializar a App
app = FastAPI(
    title="RepositóriUM Search Engine",
    description="API REST para recuperação de informação científica",
    version="1.0.0"
)

# 2. Carregar o Motor (Otimizado: tentamos carregar primeiro)
indexer = InvertedIndex()
try:
    indexer.load_index() # Evita re-indexar 110 docs a cada save do código
except:
    json_path = 'data/raw_metadata/scraper_results.json'
    indexer.create_index(json_path)

engine = QueryEngine(indexer)

# Função auxiliar para XML (REQ-B52)
def format_response(data, format_type: str):
    if format_type.lower() == "xml":
        xml = dicttoxml.dicttoxml(data, custom_root='response', attr_type=False)
        return Response(content=xml, media_type="application/xml")
    return data

@app.get("/")
def home():
    return {
        "status": "online",
        "message": "API de Recuperação de Informação pronta.",
        "docs": "/docs"
    }

@app.get("/search")
def search(q: str, method: str = "custom", format: str = "json"):
    """
    REQ-B49: Ranked results com scores
    REQ-B50: Snippets de texto
    REQ-B51: Links de acesso
    REQ-B52: JSON/XML
    """
    use_sklearn = (method.lower() == "sklearn")
    results = engine.ranked_search(q, use_sklearn=use_sklearn)
    
    query_stems = engine.processor.process_text(q)
    output = []
    
    for doc_id, score in results:
        # Garantir que acedemos à chave correta (int ou str)
        doc = indexer.documents.get(doc_id) or indexer.documents.get(str(doc_id))
        if not doc: continue

        output.append({
            "id": doc_id,
            "score": round(score, 4), # REQ-B49
            "title": doc.get("title"),
            "snippet": engine.generate_snippet(doc_id, query_stems), # REQ-B50
            "url": doc.get("pdf_url"), # REQ-B51
            "authors": doc.get("authors")
        })
    
    return format_response({"query": q, "results": output}, format)

@app.get("/boolean")
def boolean_search(q: str, format: str = "json"):
    """
    Pesquisa Booleana (AND, OR, NOT).
    """
    results_ids = engine.execute_boolean_query(q)
    
    output = []
    for doc_id in results_ids:
        doc = indexer.documents.get(doc_id) or indexer.documents.get(str(doc_id))
        if not doc: continue
        
        output.append({
            "id": doc_id,
            "title": doc.get("title"),
            "snippet": doc.get("abstract", "")[:150] + "...", # Snippet simples para boolean
            "url": doc.get("pdf_url")
        })
        
    return format_response({"query": q, "results": output}, format)

# Requisito 3.2.5: Pesquisa por Autor
@app.get("/author/{author_name}")
def search_by_author(author_name: str, format: str = "json"):
    """
    Filtra documentos por um autor específico.
    """
    results = []
    name_lower = author_name.lower()
    
    for doc_id, doc in indexer.documents.items():
        authors = doc.get("authors", [])
        # Verifica se o nome do autor está na lista de autores do doc
        if any(name_lower in a.lower() for a in doc.get("authors", [])):
            results.append({
                "id": doc_id,
                "title": doc.get("title"),
                "year": doc.get("year"),
                "url": doc.get("pdf_url"),
                "authors": authors,
                "snippet": doc.get("abstract", "")[:150] + "..."
            })
            
    if not results:
        raise HTTPException(status_code=404, detail="Nenhum documento encontrado para este autor.")
    data = {
        "author_queried": author_name,
        "total_publications": len(results),
        "publications": results
    }

    return format_response(data, format)
    