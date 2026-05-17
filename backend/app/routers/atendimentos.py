# atendimentos.py — consulta médica e anotações do prontuário

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.security import get_current_user
from ..models.models import (
    Atendimento, AnotacaoMedica, Usuario, StatusAtendimento,
    Fila, StatusFila, PerfilUsuario,
)
from ..schemas.schemas import AtendimentoCreate, AtendimentoOut, AnotacaoCreate, AnotacaoOut
from ..services.audit_service import registrar_log

router = APIRouter(prefix="/atendimentos", tags=["Atendimentos / Prontuário"])


@router.post("", response_model=AtendimentoOut, status_code=201)
async def iniciar(
    data: AtendimentoCreate,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    """Inicia atendimento (pode vincular à fila)."""
    at = Atendimento(
        paciente_id=data.paciente_id,
        profissional_id=data.profissional_id,
        agendamento_id=data.agendamento_id,
    )
    db.add(at)
    if data.fila_id:
        fila = db.query(Fila).filter(Fila.id == data.fila_id).first()
        if fila:
            fila.status = StatusFila.em_atendimento
    db.commit()
    db.refresh(at)
    await registrar_log(user.id, "INICIAR_ATENDIMENTO", "atendimentos", at.id)
    return at


@router.post("/anotacoes", response_model=AnotacaoOut, status_code=201)
async def registrar_anotacao(
    data: AnotacaoCreate,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    """Registra evolução médica (somente médico ou admin)."""
    if user.perfil not in (PerfilUsuario.medico, PerfilUsuario.admin):
        raise HTTPException(status_code=403, detail="Apenas médicos podem registrar anotações")
    nota = AnotacaoMedica(**data.model_dump())
    db.add(nota)
    db.commit()
    db.refresh(nota)
    await registrar_log(user.id, "CREATE_ANOTACAO", "anotacoes_medicas", nota.id)
    return nota


@router.patch("/{atendimento_id}/finalizar")
async def finalizar(
    atendimento_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    at = db.query(Atendimento).filter(Atendimento.id == atendimento_id).first()
    if not at:
        raise HTTPException(status_code=404)
    at.status = StatusAtendimento.finalizado
    at.fim = datetime.utcnow()
    db.commit()
    return {"ok": True}
