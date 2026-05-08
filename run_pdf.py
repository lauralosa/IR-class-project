from src.scraper.pdf_handler import PDFHandler

def main():
    handler = PDFHandler()
    # Verifica qual é o caminho correto do teu JSON (pode ser 'scraper_results.json' ou 'src/scraper/scraper_results.json')
    handler.process_pipeline('data/raw_metadata/scraper_results.json') 

if __name__ == "__main__":
    main()