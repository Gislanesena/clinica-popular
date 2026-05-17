# audit_service.py — grava logs no MongoDB

from datetime import datetime, timezone
from typing import Any, Optional
from ..core.database import get_mongo


async def registrar_log(
    usuario_id: int,
    acao: str,
    entidade: str,
    entidade_id: Optional[int] = None,
    payload: Optional[dict] = None,
    ip: str = "127.0.0.1",
):
    """Registra ação do usuário na coleção audit_logs (LGPD: só resumo no payload)."""
    try:
        db = get_mongo()
        await db.audit_logs.insert_one({
            "usuario_id": usuario_id,
            "acao": acao,
            "entidade": entidade,
            "entidade_id": entidade_id,
            "payload_resumo": payload or {},
            "ip": ip,
            "timestamp": datetime.now(timezone.utc),
        })
    except Exception:
        pass  # Mongo indisponível não impede cadastro no SQLite


async def registrar_historico_fila(doc: dict):
    """Guarda tempo real de espera para treinar ML depois."""
    try:
        db = get_mongo()
        doc["timestamp"] = datetime.now(timezone.utc)
        await db.historico_fila.insert_one(doc)
    except Exception:
        pass
