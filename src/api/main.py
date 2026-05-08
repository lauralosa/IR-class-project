from fastapi import FastAPI, Query, HTTPException, Response, Path
from fastapi.responses import JSONResponse
import time
from enum import Enum
from src.search.indexer import InvertedIndex
from src.search.query_engine import QueryEngine
from typing import Optional, List
import dicttoxml

# REQ-B66: Usar Enums garante que o utilizador só escolhe esquemas válidos
class WeightingScheme(str, Enum):
    ltc = "ltc"
    nnn = "nnn"
    lnc = "lnc"

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

@app.get("/", tags=["General"], summary="Página de Boas-vindas")
def home():
    return {
        "status": "online",
        "message": "API RepositóriUM pronta para consultas.",
        "docs": "/docs"
    }

@app.get("/search", tags=["Search"])
def search(q: str = Query(..., min_length=2, description="Termo de pesquisa (mínimo 2 caracteres)"), method: str = "custom",scheme: WeightingScheme = WeightingScheme.ltc, limit: int = Query(10, ge=1, le=50, description="Número máximo de resultados"),
    format: str = Query("json", pattern="^(json|xml)$")):
    """
    REQ-B49: Ranked results com scores
    REQ-B50: Snippets de texto
    REQ-B51: Links de acesso
    REQ-B52: JSON/XML
    """

    # --- REQ-B60: Início da medição de tempo ---
    start_time = time.perf_counter()
    
    use_sklearn = (method.lower() == "sklearn")
    results = engine.ranked_search(q, use_sklearn=use_sklearn, weighting_scheme=scheme)
    
    end_time = time.perf_counter()
    query_time = end_time - start_time
    # -------------------------------------------
    
    
    # Processamento dos resultados (Stemming/Lemma alinhado com o índice)
    # Aqui usamos a estratégia guardada no indexer para o snippet ser perfeito
    strategy = indexer.metadata.get('reduction_strategy', 'stemming')
    query_tokens = engine.processor.process_text(
        q, 
        use_stemming=(strategy == 'stemming'),
        use_lemmatization=(strategy == 'lemmatization')
    )

    output = []
    
    for doc_id, score in results:
        # Garantir que acedemos à chave correta (int ou str)
        doc = indexer.documents.get(doc_id) or indexer.documents.get(str(doc_id))
        if not doc: continue

        output.append({
            "id": doc_id,
            "score": round(score, 4), # REQ-B49
            "title": doc.get("title"),
            "snippet": engine.generate_snippet(doc_id, query_tokens), # REQ-B50
            "url": doc.get("pdf_url"), # REQ-B51
            "authors": doc.get("authors")
        })
    
    return format_response({"query": q, "search_metadata": {"query_time_sec": round(query_time, 4), "total_results": len(results),"algorithm": f"VSM with {scheme.upper()}"},"results": output}, format)

@app.get("/boolean", tags=["Search"], summary="Pesquisa Booleana")
def boolean_search(q: str = Query(..., description="Query booleana (ex: 'data AND security')"),
    format: str = "json"):
    """
    Pesquisa Booleana (AND, OR, NOT).
    """
    try:
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
            
        return format_response({"query": q,"count": len(output), "results": output}, format)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro na sintaxe da query booleana: {str(e)}")

# Requisito 3.2.5: Pesquisa por Autor
@app.get("/author/{author_name}", tags=["Authors"], summary="Listar por Autor")
def search_by_author(author_name: str = Path(..., min_length=3, description="Nome do autor para filtrar"),
    format: str = "json"):
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

# Handler global para erros inesperados
@app.exception_handler(500)
async def internal_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"message": "Erro interno no servidor de pesquisa.", "detail": str(exc)}
    )