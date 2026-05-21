from src.scraper.pdf_handler import PDFHandler

def main():
    handler = PDFHandler()
    handler.process_pipeline('data/raw_metadata/scraper_results.json') 

if __name__ == "__main__":
    main()