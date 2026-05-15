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
from pydantic import BaseModel
from src.config import settings

class UpdateIndexRequest(BaseModel):
    filepath: str

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
if not indexer.load_index(): # Evita re-indexar 110 docs a cada save do código
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
    # --- Parâmetros alinhados com o Frontend (Search.jsx) ---
    # REQ-F11: Idioma (português/inglês/ambos)
    lang: str = Query("all", pattern="^(all|PT|EN)$"),
    # REQ-F12: Técnica de processamento (stemming ou lemmatization)
    processing: str = Query("stemming", pattern="^(stemming|lemmatization)$"),
    # REQ-F15: Remoção de stop words
    stop_words: bool = True,
    # REQ-F18: Algoritmo de ordenação (custom, sklearn, boolean)
    algo: str = Query("custom", pattern="^(custom|sklearn|boolean)$"),
    # REQ-F15: Escopo da pesquisa (all, title, abstract, fulltext)
    target: str = Query("all", pattern="^(all|title|abstract|fulltext)$"),
    # REQ-F25: Área de investigação
    area: str = "all",
    # REQ-F43: Filtros de datas
    year_start: Optional[int] = Query(None),
    year_end: Optional[int] = Query(None),
    # REQ-F34: Ordenação dos Resultados
    sort_by: str = Query("relevance", pattern="^(relevance|date_desc|date_asc|title)$"),
    # REQ-F27: Modo de pesquisa por autor
    author_mode: bool = False,
    # REQ-F20: Esquema de pesos SMART (só para algoritmo custom)
    weights: WeightingScheme = WeightingScheme.ltc,
    # REQ-F31, F32: Paginação
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    # REQ-B52: Formato de Saída (JSON ou XML)
    format: str = Query("json", pattern="^(json|xml)$"),
):
    start_time = time.perf_counter()
    logger.info(f"Pesquisa recebida: q='{q}' lang={lang} processing={processing} algo={algo} target={target}")

    # --- Traduzir parâmetros do Frontend para o motor de busca ---
    use_stemming = (processing == "stemming")
    use_lemmatization = (processing == "lemmatization")
    # Mapear 'fulltext' para 'all' (o motor já indexa o texto completo)
    scope = "all" if target == "fulltext" else target

    results = []

    # --- 1. Execução da Pesquisa ---
    if author_mode:
        name_lower = q.lower()
        for doc_id, doc in indexer.documents.items():
            authors = doc.get("authors", [])
            if any(name_lower in a.lower() for a in authors):
                results.append((doc_id, 1.0))
    elif algo == "boolean":
        try:
            results_ids = engine.execute_boolean_query(q)
            results = [(doc_id, 1.0) for doc_id in results_ids]
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erro na sintaxe da query booleana: {str(e)}")
    else:
        # Modo Ranked (custom ou sklearn)
        results = engine.ranked_search(
            q,
            use_sklearn=(algo == "sklearn"),
            weighting_scheme=weights.value,
            use_stemming=use_stemming,
            use_lemmatization=use_lemmatization,
            remove_stopwords=stop_words,
            scope=scope
        )

    # --- 2. Aplicação de Filtros Globais (REQ-F16, REQ-F43) ---
    filtered_results = []
    for doc_id, score in results:
        doc = indexer.documents.get(doc_id) or indexer.documents.get(str(doc_id))
        if not doc and str(doc_id).isdigit():
            doc = indexer.documents.get(int(doc_id))
        if not doc: continue
        
        # Filtro de Área (REQ-F16)
        if area != "all" and doc.get("category", "General Engineering") != area:
            continue
            
        # Filtro de Datas (REQ-F43)
        if year_start or year_end:
            doc_year = doc.get("year", "")
            if not doc_year or not doc_year.isdigit():
                continue
            y = int(doc_year)
            if year_start and y < year_start: continue
            if year_end and y > year_end: continue
            
        # Filtro de Idioma (NOVO)
        if lang != "all" and doc.get("language") != lang:
            continue
            
        filtered_results.append((doc_id, score))

    # --- 2.5. Ordenação (REQ-F34) ---
    def get_sort_doc(d_id):
        d = indexer.documents.get(d_id) or indexer.documents.get(str(d_id))
        if not d and str(d_id).isdigit():
            d = indexer.documents.get(int(d_id))
        return d or {}

    if sort_by == "date_desc":
        filtered_results.sort(key=lambda x: get_sort_doc(x[0]).get("year", "0000") or "0000", reverse=True)
    elif sort_by == "date_asc":
        filtered_results.sort(key=lambda x: get_sort_doc(x[0]).get("year", "0000") or "0000")
    elif sort_by == "title":
        filtered_results.sort(key=lambda x: get_sort_doc(x[0]).get("title", "").lower())
    else:
        filtered_results.sort(key=lambda x: x[1], reverse=True) # Relevance (default)

    # --- 3. Lógica de Paginação Universal (REQ-F31) ---
    total_results = len(filtered_results)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_results = filtered_results[start_idx:end_idx]
    
    query_time = time.perf_counter() - start_time

    # --- 4. Formatação da Saída Final ---
    output = []
    for doc_id, score in paginated_results:
        doc = indexer.documents.get(doc_id) or indexer.documents.get(str(doc_id))
        if not doc and str(doc_id).isdigit():
            doc = indexer.documents.get(int(doc_id))
        if not doc: doc = {}
        snippet = doc.get("abstract", "")[:200] + "..." if author_mode else engine.generate_snippet(doc_id, q)
        output.append({
            "id": doc_id,
            "score": round(score, 4),
            "title": doc.get("title"),
            "year": doc.get("year"),
            "snippet": snippet,
            "url": doc.get("pdf_url"),
            "authors": doc.get("authors", []),
            "category": doc.get("category", "General Engineering")
        })

    return format_response({
        "metadata": {
            "total": total_results,
            "page": page,
            "page_size": page_size,
            "time": round(query_time, 4),
            "config": {
                "lang": lang,
                "processing": processing,
                "stop_words": stop_words,
                "algo": "author" if author_mode else algo,
                "scope": scope,
                "weights": weights.value if not author_mode and algo != "boolean" else "N/A",
                "area": area,
                "year_start": year_start,
                "year_end": year_end,
                "sort_by": sort_by
            }
        },
        "results": output
    }, format)

@app.get("/stats", tags=["System"], summary="Estatísticas do Índice (Admin Dashboard)")
def get_stats():
    """REQ-F55, F56: Retorna métricas do motor para o Dashboard do Frontend."""
    return {
        "num_docs": indexer.num_docs,
        "vocabulary_size": len(indexer.index),
        "author_count": len(indexer.author_index),
        "metadata": indexer.metadata
    }

@app.post("/index/update", tags=["System"], summary="Atualização Incremental do Índice")
def update_index_endpoint(req: UpdateIndexRequest):
    """
    REQ-B31: Atualiza o índice iterativamente com novos documentos via API.
    """
    if not os.path.exists(req.filepath):
        raise HTTPException(status_code=404, detail="Ficheiro JSON não encontrado no caminho especificado.")
    try:
        indexer.update_index(req.filepath)
        return {"status": "sucesso", "mensagem": f"Índice atualizado. Total de documentos: {indexer.num_docs}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Handler global para erros inesperados
@app.exception_handler(500)
async def internal_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"message": "Erro interno no servidor de pesquisa.", "detail": str(exc)}
    )