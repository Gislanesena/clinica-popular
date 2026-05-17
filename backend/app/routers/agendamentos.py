# agendamentos.py — marcar e cancelar consultas

from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ..core.database import get_db
from ..core.security import get_current_user
from ..models.models import Agendamento, Paciente, Usuario, StatusAgendamento
from ..schemas.schemas import AgendamentoCreate, AgendamentoOut
from ..services.ml_service import ml_service
from ..services.audit_service import registrar_log

router = APIRouter(prefix="/agendamentos", tags=["Agendamentos"])


@router.get("", response_model=List[AgendamentoOut])
def listar(
    data: Optional[date] = None,
    profissional_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    """Lista agendamentos do dia ou por profissional."""
    q = db.query(Agendamento).filter(Agendamento.status.notin_([StatusAgendamento.cancelado]))
    if data:
        q = q.filter(Agendamento.data_hora >= datetime.combine(data, datetime.min.time()))
        q = q.filter(Agendamento.data_hora < datetime.combine(data, datetime.max.time()))
    if profissional_id:
        q = q.filter(Agendamento.profissional_id == profissional_id)
    items = q.order_by(Agendamento.data_hora).all()
    result = []
    for a in items:
        out = AgendamentoOut.model_validate(a)
        out.paciente_nome = a.paciente.nome if a.paciente else None
        out.prob_noshow = float(a.prob_noshow or 0)
        result.append(out)
    return result


@router.post("", response_model=AgendamentoOut, status_code=201)
async def criar(
    data: AgendamentoCreate,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    """Cria agendamento; ML calcula probabilidade de falta."""
    conflito = db.query(Agendamento).filter(
        Agendamento.profissional_id == data.profissional_id,
        Agendamento.data_hora == data.data_hora,
        Agendamento.status.notin_([StatusAgendamento.cancelado, StatusAgendamento.faltou]),
    ).first()
    if conflito:
        raise HTTPException(status_code=409, detail="Horário já ocupado para este profissional")

    paciente = db.query(Paciente).filter(Paciente.id == data.paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")

    idade = (date.today() - paciente.data_nascimento).days // 365
    faltas = db.query(Agendamento).filter(
        Agendamento.paciente_id == paciente.id,
        Agendamento.status == StatusAgendamento.faltou,
    ).count()

    prob = ml_service.prever_noshow(
        data.data_hora.weekday(),
        data.data_hora.hour,
        idade,
        faltas,
        0,
    )

    ag = Agendamento(
        paciente_id=data.paciente_id,
        profissional_id=data.profissional_id,
        usuario_id=user.id,
        data_hora=data.data_hora,
        observacoes=data.observacoes,
        prob_noshow=prob,
    )
    db.add(ag)
    db.commit()
    db.refresh(ag)
    await registrar_log(user.id, "CREATE_AGENDAMENTO", "agendamentos", ag.id)
    out = AgendamentoOut.model_validate(ag)
    out.paciente_nome = paciente.nome
    out.prob_noshow = float(prob)
    return out


@router.patch("/{agendamento_id}/cancelar")
async def cancelar(
    agendamento_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    ag = db.query(Agendamento).filter(Agendamento.id == agendamento_id).first()
    if not ag:
        raise HTTPException(status_code=404)
    ag.status = StatusAgendamento.cancelado
    db.commit()
    await registrar_log(user.id, "CANCEL_AGENDAMENTO", "agendamentos", ag.id)
    return {"ok": True}
