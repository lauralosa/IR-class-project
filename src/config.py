from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "RepositóriUM"
    ENV: str = "development"
    DEBUG: bool = True
    
    STORAGE_DIR: str = "data"
    INDEX_FILE: str = "data/index.json"
    RAW_DATA_PATH: str = "data/raw_metadata/scraper_results.json"
    
    DEFAULT_BATCH_SIZE: int = 50

    # Procura o ficheiro .env na raiz
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()