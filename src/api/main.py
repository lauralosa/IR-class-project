from fastapi import FastAPI, Query, HTTPException, Response, Path
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import time
from enum import Enum
from src.search.indexer import InvertedIndex
from src.search.query_engine import QueryEngine
from typing import Optional, List
import dicttoxml
import logging
import os
from src.config import settings

# Configuração do Logger (REQ-B69)
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("system.log"), # Escreve no ficheiro
        logging.StreamHandler()            # Escreve no terminal
    ]
)
logger = logging.getLogger("API-REPOSITORIUM")




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
logger.info(f"Sistema {settings.APP_NAME} a iniciar em modo {settings.ENV}...")

# 2. ADICIONAR O CORS AQUI (REQ-F75)
# Isto permite que o React da tua colega consiga ler os teus dados
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], # Portas comuns do Vite/React
    allow_credentials=True,
    allow_methods=["*"], # Permite GET, POST, etc.
    allow_headers=["*"], # Permite todos os headers (importante para JSON)
)

# 2. Carregar o Motor (Otimizado: tentamos carregar primeiro)
indexer = InvertedIndex()
# HACK: Corrige o bug do try/except da Laura
if not indexer.load_index():
    print("Índice não encontrado! A iniciar criação de um novo índice...")
    json_path = settings.RAW_DATA_PATH
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
def search(
    q: str = Query(..., min_length=2),
    # REQ-F11, F12: Parâmetros de processamento dinâmico
    stemming: bool = True,
    lemmatization: bool = False,
    stopwords: bool = True,
    # REQ-F15: Escopo da pesquisa
    scope: str = Query("all", pattern="^(all|title|abstract)$"),
    # REQ-F31, F32: Paginação
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    # REQ-F18, F20: Algoritmo e Pesos
    method: str = "custom",
    scheme: WeightingScheme = WeightingScheme.ltc
):
    start_time = time.perf_counter()
    
    # 1. Executa a pesquisa (O motor precisa de aceitar estes novos filtros)
    results = engine.ranked_search(
        q, 
        use_stemming=stemming, 
        use_lemmatization=lemmatization,
        remove_stopwords=stopwords,
        scope=scope # Precisamos de implementar este filtro no engine
    )
    
    # 2. Lógica de Paginação (REQ-F31)
    total_results = len(results)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_results = results[start_idx:end_idx]
    
    query_time = time.perf_counter() - start_time

    # 3. Formatação da resposta para o Frontend
    output = []
    for doc_id, score in paginated_results:
        doc = indexer.documents.get(str(doc_id))
        if not doc: continue
        output.append({
            "id": doc_id,
            "score": round(score, 4),
            "title": doc.get("title"),
            "year": doc.get("year"), # REQ-F25
            "snippet": engine.generate_snippet(doc_id, q), # REQ-F26
            "url": doc.get("pdf_url"), # REQ-F27
            "authors": doc.get("authors") # REQ-F24
        })

    return {
        "metadata": {
            "total": total_results,
            "page": page,
            "page_size": page_size,
            "time": round(query_time, 4),
            "config": {"stemming": stemming, "lemma": lemmatization, "scope": scope}
        },
        "results": output
    }
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