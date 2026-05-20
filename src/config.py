# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "RepositóriUM"
    ENV: str = "development"
    DEBUG: bool = True
    
    STORAGE_DIR: str = "data"
    INDEX_FILE_STEMMING: str = "data/indexes/index_stemming.json"
    INDEX_FILE_LEMMATIZATION: str = "data/indexes/index_lemmatization.json"
    INDEX_FILE: str = "data/indexes/index_stemming.json"  # alias por compatibilidade
    RAW_DATA_PATH: str = "data/raw_metadata/scraper_results.json"
    PDF_STORAGE_PATH: str = "data/pdfs"
    TXT_STORAGE_PATH: str = "data/extracted_text"
    
    DEFAULT_BATCH_SIZE: int = 50
    DEFAULT_SCHEME: str = "ltc"

    # Carrega automaticamente do ficheiro .env
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()