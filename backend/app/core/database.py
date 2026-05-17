# database.py — conexão com SQLite (SQL) e MongoDB (logs)

from pathlib import Path
from sqlalchemy import create_engine  # Motor de conexão SQL
from sqlalchemy.orm import sessionmaker, DeclarativeBase  # Sessões e base dos modelos
from motor.motor_asyncio import AsyncIOMotorClient  # Cliente assíncrono MongoDB
from .config import settings


def _criar_engine():
    """Cria o engine SQLAlchemy conforme o tipo de banco na URL."""
    url = settings.DATABASE_URL
    kwargs = {}
    if url.startswith("sqlite"):
        # SQLite exige isso quando várias threads acessam (FastAPI)
        kwargs["connect_args"] = {"check_same_thread": False}
        # Garante que a pasta do arquivo .db existe
        caminho = url.replace("sqlite:///", "").lstrip("/")
        if caminho and caminho != ":memory:":
            Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    else:
        kwargs["pool_pre_ping"] = True
    return create_engine(url, **kwargs)


engine = _criar_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

mongo_client: AsyncIOMotorClient | None = None  # Preenchido no startup da API


class Base(DeclarativeBase):
    """Classe base de todos os modelos SQLAlchemy (tabelas SQLite)."""
    pass


def get_db():
    """Dependência FastAPI: abre sessão SQL e fecha ao terminar a requisição."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_mongo():
    """Retorna o banco MongoDB usado para auditoria e histórico da fila."""
    return mongo_client[settings.MONGODB_DB]


async def connect_mongo():
    """Conecta ao MongoDB quando a API inicia."""
    global mongo_client
    mongo_client = AsyncIOMotorClient(settings.MONGODB_URL)


async def close_mongo():
    """Encerra conexão MongoDB quando a API desliga."""
    global mongo_client
    if mongo_client:
        mongo_client.close()
