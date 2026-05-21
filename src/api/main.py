from fastapi import FastAPI, Query, HTTPException, Response, Path
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import time
from enum import Enum
from src.search.indexer import InvertedIndex
from src.search.query_engine import QueryEngine
from typing import Optional, List
# pyrefly: ignore [missing-import]
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

# 2. Carregar os dois motores — stemming e lematização (REQ-B18, REQ-B57)
logger.info("A carregar índice de stemming...")
indexer_stem = InvertedIndex()
if not indexer_stem.load_index(settings.INDEX_FILE_STEMMING):
    logger.info("Índice de stemming não encontrado. A criar (pode demorar)...")
    indexer_stem.create_index(settings.RAW_DATA_PATH, strategy="stemming")

logger.info("A carregar índice de lematização...")
indexer_lemma = InvertedIndex()
if not indexer_lemma.load_index(settings.INDEX_FILE_LEMMATIZATION):
    logger.info("Índice de lematização não encontrado. A criar (pode demorar)...")
    indexer_lemma.create_index(settings.RAW_DATA_PATH, strategy="lemmatization")

engine_stem = QueryEngine(indexer_stem)
engine_lemma = QueryEngine(indexer_lemma)

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
    processing: str = Query("stemming", pattern="^(stemming|lemmatization|none)$"),
    # REQ-F15: Remoção de stop words
    stop_words: bool = True,
    # REQ-F18: Algoritmo de ordenação (custom, sklearn, boolean)
    algo: str = Query("custom", pattern="^(custom|sklearn|boolean)$"),
    # REQ-F15: Escopo da pesquisa (all, title, abstract, fulltext)
    target: str = Query("all", pattern="^(all|title|abstract|fulltext)$"),
    # REQ-F25: Área de investigação
    area: str = "all",
    # REQ-F44: Tipo de Documento
    doc_type: str = "all",
    # REQ-F45: Filtro por Keyword
    keyword: str = "all",
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
    # Selecionar o índice e motor correto com base na estratégia (REQ-B18, REQ-B57)
    indexer = indexer_lemma if processing == "lemmatization" else indexer_stem
    engine = engine_lemma if processing == "lemmatization" else engine_stem

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
            
        # Inferência de Tipo de Documento (REQ-F44)
        text_for_type = (doc.get("title", "") + " " + doc.get("abstract", "")).lower()
        if "doutoramento" in text_for_type or "phd" in text_for_type or "tese" in text_for_type or "thesis" in text_for_type:
            current_type = "phd"
        elif "mestrado" in text_for_type or "master" in text_for_type or "msc" in text_for_type or "dissertação" in text_for_type or "dissertation" in text_for_type:
            current_type = "msc"
        else:
            current_type = "article"
            
        # Atribuímos ao documento em tempo real para ser retornado
        doc["inferred_type"] = current_type
            
        if doc_type != "all" and current_type != doc_type:
            continue
            
        # Filtro de Keyword (REQ-F45)
        doc_keywords = [k.lower().strip() for k in doc.get("keywords", [])]
        if keyword != "all" and keyword.lower() not in doc_keywords:
            continue
            
        # Filtro de Datas (REQ-F43)
        if year_start or year_end:
            import re as _re
            doc_year_raw = str(doc.get("year", "") or doc.get("date", ""))
            # Extrair o primeiro número de 4 dígitos que comece por 1 ou 2
            year_match = _re.search(r'\b(1|2)\d{3}\b', doc_year_raw)
            if not year_match:
                continue
            y = int(year_match.group())
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

    # --- 2.75 Facetas de Keywords (REQ-F45) ---
    keyword_counts = {}
    for doc_id, score in filtered_results:
        d = get_sort_doc(doc_id)
        kws = d.get("keywords", [])
        for k in kws:
            kw_clean = k.lower().strip()
            if kw_clean:
                keyword_counts[kw_clean] = keyword_counts.get(kw_clean, 0) + 1
    
    top_keywords = [{"keyword": k, "count": c} for k, c in sorted(keyword_counts.items(), key=lambda item: item[1], reverse=True)[:15]]

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
            "abstract": doc.get("abstract", ""),
            "url": doc.get("pdf_url"),
            "authors": doc.get("authors", []),
            "category": doc.get("category", "General Engineering"),
            "doc_type": doc.get("inferred_type", "article"),
            "keywords": doc.get("keywords", [])
        })

    return format_response({
        "metadata": {
            "total": total_results,
            "page": page,
            "page_size": page_size,
            "time": round(query_time, 4),
            "facets": {
                "keywords": top_keywords
            },
            "config": {
                "lang": lang,
                "processing": processing,
                "stop_words": stop_words,
                "algo": "author" if author_mode else algo,
                "scope": scope,
                "weights": weights.value if not author_mode and algo != "boolean" else "N/A",
                "area": area,
                "doc_type": doc_type,
                "keyword": keyword,
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
    indexer = indexer_stem  # usa o índice de stemming como referência principal
    
    # REQ-F57: Calcular os top termos no vocabulário (com base no DF)
    term_counts = []
    for term, postings in indexer.index.items():
        if len(term) > 3: # Ignorar termos muito curtos
            term_counts.append({"term": term, "df": len(postings)})
            
    top_terms = sorted(term_counts, key=lambda x: x["df"], reverse=True)[:10]

    # Contagem de categorias para REQ-F58
    categories = {}
    for doc in indexer.documents.values():
        cat = doc.get("category", "General Engineering")
        categories[cat] = categories.get(cat, 0) + 1

    return {
        "num_docs": indexer.num_docs,
        "vocabulary_size": {
            "stemming": len(indexer_stem.index),
            "lemmatization": len(indexer_lemma.index)
        },
        "author_count": len(indexer.author_index),
        "metadata": indexer.metadata,
        "performance": {
            "stemming_time_sec": indexer_stem.metadata.get("performance", {}).get("indexing_time_sec", 0),
            "lemmatization_time_sec": indexer_lemma.metadata.get("performance", {}).get("indexing_time_sec", 0)
        },
        "top_terms": top_terms,
        "categories": categories
    }

# --- REQ-F35 a F38: Endpoints de Autores ---

@app.get("/authors", tags=["Authors"], summary="Listar/Pesquisar Autores")
def list_authors(
    q: Optional[str] = Query(None, description="Filtrar autores por nome"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    REQ-F35: Lista todos os autores com contagem de publicações.
    Suporta pesquisa por nome.
    """
    indexer = indexer_stem  # dados de autores são iguais nos dois índices
    all_authors = []
    for author_name, doc_ids in indexer.author_index.items():
        if q and q.lower() not in author_name.lower():
            continue
        all_authors.append({
            "name": author_name,
            "publication_count": len(doc_ids)
        })

    # Ordenar por número de publicações (desc)
    all_authors.sort(key=lambda x: x["publication_count"], reverse=True)

    total = len(all_authors)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = all_authors[start:end]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "authors": paginated
    }


@app.get("/authors/{author_name}", tags=["Authors"], summary="Perfil de Autor")
def get_author_profile(author_name: str = Path(..., description="Nome do autor")):
    """
    REQ-F35 a F38: Retorna o perfil completo de um autor:
    - Lista de publicações
    - Colaboradores (co-autores)
    - Timeline de publicações por ano
    """
    indexer = indexer_stem  # dados de autores são iguais nos dois índices
    # Procura fuzzy: encontra o autor mais próximo do nome pedido
    matched_author = None
    for name in indexer.author_index.keys():
        if author_name.lower() == name.lower():
            matched_author = name
            break
    if not matched_author:
        # Tenta procura parcial
        for name in indexer.author_index.keys():
            if author_name.lower() in name.lower():
                matched_author = name
                break

    if not matched_author:
        raise HTTPException(status_code=404, detail=f"Autor '{author_name}' não encontrado.")

    doc_ids = indexer.author_index[matched_author]

    # Publicações do autor
    publications = []
    co_authors_counter = {}
    year_counts = {}
    categories_counter = {}

    for doc_id in doc_ids:
        doc = indexer.documents.get(doc_id) or indexer.documents.get(str(doc_id))
        if not doc:
            continue

        year = doc.get("year", "N/D")
        category = doc.get("category", "General Engineering")

        publications.append({
            "id": doc_id,
            "title": doc.get("title", "Sem título"),
            "year": year,
            "url": doc.get("pdf_url"),
            "authors": doc.get("authors", []),
            "category": category,
            "snippet": (doc.get("abstract", "") or "")[:200] + "..."
        })

        # Contar co-autores (REQ-F38)
        for co_author in doc.get("authors", []):
            if co_author != matched_author:
                co_authors_counter[co_author] = co_authors_counter.get(co_author, 0) + 1

        # Timeline por ano (REQ-F37)
        if year and str(year).isdigit():
            year_counts[str(year)] = year_counts.get(str(year), 0) + 1

        # Contagem por categoria
        categories_counter[category] = categories_counter.get(category, 0) + 1

    # Ordenar publicações por ano (mais recentes primeiro)
    publications.sort(key=lambda x: x["year"] or "0000", reverse=True)

    # Top co-autores ordenados por nº de colaborações
    top_collaborators = [
        {"name": name, "shared_papers": count}
        for name, count in sorted(co_authors_counter.items(), key=lambda x: x[1], reverse=True)
    ]

    # Timeline ordenada cronologicamente
    timeline = [
        {"year": yr, "count": cnt}
        for yr, cnt in sorted(year_counts.items())
    ]

    return {
        "author": matched_author,
        "publication_count": len(publications),
        "publications": publications,
        "collaborators": top_collaborators[:20],  # Top 20 colaboradores
        "timeline": timeline,
        "categories": categories_counter
    }

@app.post("/index/update", tags=["System"], summary="Atualização Incremental do Índice")
def update_index_endpoint(req: UpdateIndexRequest):
    """
    REQ-B31: Atualiza o índice iterativamente com novos documentos via API.
    """
    if not os.path.exists(req.filepath):
        raise HTTPException(status_code=404, detail="Ficheiro JSON não encontrado no caminho especificado.")
    try:
        indexer_stem.update_index(req.filepath)
        indexer_lemma.update_index(req.filepath)
        return {"status": "sucesso", "mensagem": f"Ambos os índices atualizados. Total: {indexer_stem.num_docs} documentos."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Handler global para erros inesperados
@app.exception_handler(500)
async def internal_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"message": "Erro interno no servidor de pesquisa.", "detail": str(exc)}
    )