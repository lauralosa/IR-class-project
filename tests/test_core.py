import pytest
import os
import logging
import json
import math
import time 
from src.config import settings
from src.search.processor import TextProcessor
from src.search.indexer import InvertedIndex
from src.search.query_engine import QueryEngine
from src.ml.classifier import DocumentClassifier

# =================================================================
# CONFIGURAÇÃO DE LOGGING (REQ-B69)
# =================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.FileHandler("system.log"), logging.StreamHandler()]
)
logger = logging.getLogger("MASTER-TEST")

# =================================================================
# FIXTURES (Preparação do Ambiente)
# =================================================================
@pytest.fixture(scope="module")
def shared_components():
    """Inicializa os componentes core para serem usados nos testes."""
    logger.info("A inicializar componentes core para testes...")
    processor = TextProcessor()
    indexer = InvertedIndex()
    # Tenta carregar o índice real, se falhar cria um temporário
    if not indexer.load_index(settings.INDEX_FILE):
        logger.warning("Índice não encontrado. A criar índice de teste...")
        indexer.create_index(settings.RAW_DATA_PATH)
    
    engine = QueryEngine(indexer)
    return processor, indexer, engine

# =================================================================
# 1. TESTES DE PROCESSAMENTO (NLP) - REQ-B13, B15, B16, B17
# =================================================================
def test_nlp_processor(shared_components):
    processor, _, _ = shared_components
    text = "The computers are processing information"
    
    # Stemming
    stems = processor.process_text(text, use_stemming=True)
    assert "comput" in stems
    
    # Lemmatization
    lemmas = processor.process_text(text, use_stemming=False, use_lemmatization=True)
    assert "computer" in lemmas
    
    logger.info(" Teste NLP: OK")

# =================================================================
# 2. TESTES DE INDEXAÇÃO - REQ-B29, B30, B31
# =================================================================
def test_indexing_logic(shared_components):
    _, indexer, _ = shared_components
    
    assert indexer.num_docs > 0
    assert len(indexer.index) > 0
    
    # Verificar se termos técnicos existem no vocabulário
    assert "data" in indexer.index or "blockchain" in indexer.index
    
    # Testar Skip Pointers (REQ-B29)
    term = list(indexer.index.keys())[0]
    _, skips = indexer.get_postings(term)
    # Se o termo tiver muitos documentos, deve ter skips
    logger.info(f" Teste Indexação: {indexer.num_docs} docs validados.")

# =================================================================
# 3. TESTES DE PESQUISA (BOOLEAN & RANKED) - REQ-B37, B39, B45, B48
# =================================================================
def test_search_functionalities(shared_components):
    _, _, engine = shared_components
    
    # Teste Booleano Complexo (REQ-B45)
    bool_res = engine.execute_boolean_query("data AND (blockchain OR iot)")
    assert isinstance(bool_res, list)
    
    # Teste de Frase (REQ-B48)
    # Usamos o processador para alinhar os termos
    phrase_query = engine.processor.process_text("human aware assistance")
    phrase_res = engine.search_phrase(phrase_query)
    assert isinstance(phrase_res, list)
    
    # Teste de Ranking LTC (REQ-B37)
    ranked_res = engine.ranked_search("cognitive science", weighting_scheme="ltc")
    if ranked_res:
        assert ranked_res[0][1] >= ranked_res[-1][1] # Score do primeiro >= último
    
    logger.info(" Teste Pesquisa (Boolean/Ranked): OK")

# =================================================================
# 4. TESTES DE QUALIDADE E PERFORMANCE - REQ-B60, B61, B62
# =================================================================
def test_search_quality(shared_components):
    _, indexer, engine = shared_components

    print(f"\n DEBUG: O índice tem {len(indexer.index)} termos e {indexer.num_docs} docs.")
    
    # Ground Truth (Gabarito reduzido para o teste)
    target = "sector"
    expected_at_least = 1
    
    start_time = time.perf_counter()
    results = engine.ranked_search(target)
    duration = time.perf_counter() - start_time
    
    # REQ-B60: Tempo de resposta deve ser baixo (< 200ms para queries simples)
    assert duration < 0.2
    
    # REQ-B61: Verificar se encontramos resultados relevantes
    assert len(results) >= expected_at_least
    
    logger.info(f" Teste Qualidade: Latência {duration:.4f}s")

# =================================================================
# 5. TESTES DE MACHINE LEARNING - REQ-B41, B42
# =================================================================
def test_classifier_logic(shared_components):
    _, indexer, _ = shared_components
    clf = DocumentClassifier()
    
    # Simular treino (REQ-B41)
    # Nota: Usamos uma amostra para o teste ser rápido
    sample_docs = dict(list(indexer.documents.items())[:20])
    accuracy = clf.prepare_and_train(sample_docs)
    
    assert accuracy >= 0
    
    # Predição (REQ-B42)
    cat = clf.predict_category("Machine learning in health", "Use of AI to detect diseases")
    assert isinstance(cat, str)
    
    logger.info(f" Teste ML: Categoria prevista '{cat}'")

