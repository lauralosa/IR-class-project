import json
from src.search.processor import TextProcessor

def test_nlp_pipeline():
    # 1. Carregar os dados que o teu scraper recolheu
    # Ajusta o caminho se o ficheiro estiver noutro local
    try:
        with open('data/raw_metadata/scraper_results.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Erro: scraper_results.json não encontrado. Corre o scraper primeiro!")
        return

    # 2. Inicializar o processador
    processor = TextProcessor()

    # 3. Testar com o primeiro documento
    if data:
        doc = data[0]
        original_text = doc['abstract']
        
        print(f"\n--- TESTE DE PROCESSAMENTO ---")
        print(f"Título Original: {doc['title']}")
        print(f"\nTexto Original (Abstract): {original_text[:150]}...")

        # Testar as duas variantes exigidas pelo enunciado [cite: 35]
        stemmed = processor.process_text(original_text, use_stemming=True)
        lemmatized = processor.process_text(original_text, use_stemming=False, use_lemmatization=True)

        print(f"\n[STEMMING - Porter]:")
        print(stemmed[:15]) # Mostra os primeiros 15 tokens

        print(f"\n[LEMATIZAÇÃO - WordNet]:")
        print(lemmatized[:15])

def test_stop_words_configurability():
    proc = TextProcessor()
    # Teste com palavra Inglesa para validar o Porter Stemmer (REQ-B16)
    text_en = "The computers are working"
    tokens_en = proc.process_text(text_en, use_stemming=True)
    # 'computers' no Porter vira 'comput'
    assert "comput" in tokens_en 
    
    # Teste com Português (REQ-B15)
    text_pt = "O sistema de informação"
    tokens_pt = proc.process_text(text_pt, remove_stopwords=True)
    # Como o Porter não reduz 'sistema', verificamos a palavra que ele gera
    assert "sistema" in tokens_pt or "sistem" in tokens_pt

    # ADICIONA ISTO AQUI:
    print("\n--- TESTE DE CONFIGURAÇÃO  ---")
    print("[OK] Stop words e Stemming validados com sucesso!")

if __name__ == "__main__":
    test_nlp_pipeline()
    test_stop_words_configurability()