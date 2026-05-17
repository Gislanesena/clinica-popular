# fila_service.py — regras de ordenação e prioridade da fila

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models.models import Fila, StatusFila, PrioridadeFila, Paciente, Profissional
from .ml_service import ml_service

# Ordem: menor número = atendido primeiro
PRIORIDADE_ORDEM = {
    PrioridadeFila.emergencia: 0,
    PrioridadeFila.gestante: 1,
    PrioridadeFila.idoso: 2,
    PrioridadeFila.pcd: 3,
    PrioridadeFila.normal: 4,
}


def calcular_idade_prioridade(paciente: Paciente) -> PrioridadeFila:
    """Define prioridade automática para idosos (≥60 anos ou flag prioritario)."""
    if paciente.prioritario:
        return PrioridadeFila.idoso
    hoje = datetime.now().date()
    idade = (hoje - paciente.data_nascimento).days // 365
    if idade >= 60:
        return PrioridadeFila.idoso
    return PrioridadeFila.normal


def proxima_posicao(db: Session) -> int:
    """Próximo número de senha na fila."""
    max_pos = db.query(func.max(Fila.posicao)).filter(
        Fila.status.in_([StatusFila.aguardando, StatusFila.chamado])
    ).scalar()
    return (max_pos or 0) + 1


def tamanho_fila(db: Session) -> int:
    """Quantos pacientes aguardando agora."""
    return db.query(Fila).filter(Fila.status == StatusFila.aguardando).count()


def listar_fila_ordenada(db: Session) -> list:
    """Lista fila por prioridade e depois por ordem de chegada."""
    itens = db.query(Fila).filter(
        Fila.status.in_([StatusFila.aguardando, StatusFila.chamado])
    ).all()
    return sorted(itens, key=lambda f: (PRIORIDADE_ORDEM.get(f.prioridade, 5), f.posicao))


def mascarar_cpf(cpf: str) -> str:
    """Oculta parte do CPF na fila pública (LGPD)."""
    digits = "".join(c for c in cpf if c.isdigit())
    if len(digits) >= 11:
        return f"{digits[:3]}.***.***-{digits[-2:]}"
    return "***"
