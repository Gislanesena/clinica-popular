# config.py — variáveis de ambiente e configurações globais da API

from pydantic_settings import BaseSettings  # Lê variáveis do .env e valida tipos


class Settings(BaseSettings):
    """Configurações carregadas automaticamente do arquivo .env ou do Docker."""

    APP_NAME: str = "Clínica Popular PEP"  # Nome exibido na documentação
    # Banco SQL principal: SQLite (arquivo .db)
    DATABASE_URL: str = "sqlite:///./data/clinica.db"
    MONGODB_URL: str = "mongodb://localhost:27017"  # Logs de auditoria
    MONGODB_DB: str = "clinica_popular"
    SECRET_KEY: str = "chave-secreta-trocar-em-producao-clinica-popular-2026"  # Assina JWT
    ALGORITHM: str = "HS256"  # Algoritmo do token JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # Token válido por 8 horas
    ML_MODELS_PATH: str = "../ml/models"  # Pasta dos modelos .pkl

    class Config:
        env_file = ".env"  # Arquivo opcional na pasta backend/


settings = Settings()  # Instância única usada em todo o projeto
