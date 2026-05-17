# dashboard.py — indicadores e alertas de ML

from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..core.database import get_db
from ..core.security import get_current_user
from ..models.models import (
    Paciente, Agendamento, Fila, Atendimento, Usuario,
    StatusFila, StatusAtendimento, StatusAgendamento,
)
from ..schemas.schemas import DashboardOut, PredicaoNoshowOut
from ..services.ml_service import ml_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard / ML"])


@router.get("", response_model=DashboardOut)
def indicadores(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    """Resumo do dia: pacientes, fila, atendimentos, taxa de falta."""
    hoje = date.today()
    inicio = datetime.combine(hoje, datetime.min.time())

    total_pac = db.query(func.count(Paciente.id)).scalar() or 0
    ag_hoje = db.query(func.count(Agendamento.id)).filter(
        Agendamento.data_hora >= inicio
    ).scalar() or 0
    na_fila = db.query(func.count(Fila.id)).filter(Fila.status == StatusFila.aguardando).scalar() or 0
    atendidos = db.query(func.count(Atendimento.id)).filter(
        Atendimento.inicio >= inicio,
        Atendimento.status == StatusAtendimento.finalizado,
    ).scalar() or 0

    tempo_medio = db.query(func.avg(Fila.tempo_espera_estimado_min)).filter(
        Fila.status == StatusFila.aguardando
    ).scalar() or 30.0

    total_ag = db.query(func.count(Agendamento.id)).filter(
        Agendamento.data_hora >= inicio - timedelta(days=30)
    ).scalar() or 1
    faltas = db.query(func.count(Agendamento.id)).filter(
        Agendamento.status == StatusAgendamento.faltou,
        Agendamento.data_hora >= inicio - timedelta(days=30),
    ).scalar() or 0

    return DashboardOut(
        total_pacientes=total_pac,
        agendamentos_hoje=ag_hoje,
        na_fila_agora=na_fila,
        atendidos_hoje=atendidos,
        tempo_medio_espera_min=round(float(tempo_medio), 1),
        taxa_falta_pct=round(100.0 * faltas / max(total_ag, 1), 1),
    )


@router.get("/risco-falta", response_model=list[PredicaoNoshowOut])
def risco_falta(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    """Agendamentos de hoje com alto risco de no-show."""
    hoje = date.today()
    inicio = datetime.combine(hoje, datetime.min.time())
    fim = datetime.combine(hoje, datetime.max.time())
    ags = db.query(Agendamento).filter(
        Agendamento.data_hora >= inicio,
        Agendamento.data_hora <= fim,
        Agendamento.status.in_([StatusAgendamento.agendado, StatusAgendamento.confirmado]),
    ).all()
    result = []
    for a in ags:
        prob = float(a.prob_noshow or 0)
        if prob >= 0.35:
            result.append(PredicaoNoshowOut(
                agendamento_id=a.id,
                prob_noshow=prob,
                risco=ml_service.risco_label(prob),
            ))
    return sorted(result, key=lambda x: -x.prob_noshow)


@router.get("/profissionais")
def profissionais(db: Session = Depends(get_db)):
    """Lista profissionais ativos (uso em selects)."""
    from ..models.models import Profissional
    return db.query(Profissional).filter(Profissional.ativo == True).all()
