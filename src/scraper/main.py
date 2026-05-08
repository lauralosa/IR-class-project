import json
import scraper
import logging
import os
from src.config import settings

# Configuração do Logger 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("system.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SCRAPER-MAIN")

def main():

    logger.info("Iniciando o processo de Web Scraping ...")

    # Example collection:  https://repositorium.uminho.pt/collections/690f7814-a67b-4f27-8fff-6b33581d1a91/search
    # https://repositorium.uminho.pt/handle/1822/21293
    repo_url = f"https://repositorium.uminho.pt/handle/"
    collection = "1822/14400"
    base_url = f"{repo_url}/{collection}"

    try:
        # Create an instance of the Scraper class
        # The scraper will automatically detect Chrome in default locations
        scraper_instance = scraper.UMinhoDSpace8Scraper(base_url, max_items=110)
        final_results = scraper_instance.scrape()

        logger.info(f"Scraping concluído com sucesso. Total: {len(final_results)} artigos.")

        # Garantir que a pasta de destino existe (REQ-B67)
        output_path = settings.RAW_DATA_PATH
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        # Guardar resultados (REQ-B08: Robust Error Handling)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, ensure_ascii=False, indent=4)

        logger.info(f"Dados guardados em: {output_path}")

    except Exception as e:
            logger.error(f"Erro crítico durante o scraping: {str(e)}")
            raise

if __name__ == "__main__":
    main()