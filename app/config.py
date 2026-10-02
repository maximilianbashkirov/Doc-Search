from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Настройки PostgreSQL
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "search_db"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432

    # Настройки Elasticsearch
    ELASTIC_HOST: str = "elasticsearch"
    ELASTIC_PORT: int = 9200
    ELASTIC_INDEX: str = "documents_index"

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def elastic_url(self) -> str:
        return f"http://{self.ELASTIC_HOST}:{self.ELASTIC_PORT}"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
