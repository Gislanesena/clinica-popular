# fila.py — fila inteligente com prioridade e ML

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..core.database import get_db
from ..core.security import get_current_user
from ..models.models import Fila, Paciente, Profissional, Usuario, StatusFila, Agendamento, StatusAgendamento
from ..schemas.schemas import FilaEntrada, FilaOut
from ..services.fila_service import (
    proxima_posicao, tamanho_fila, listar_fila_ordenada,
    calcular_idade_prioridade, mascarar_cpf,
)
from ..services.ml_service import ml_service
from ..services.audit_service import registrar_log, registrar_historico_fila

router = APIRouter(prefix="/fila", tags=["Fila Inteligente"])


def _to_out(f: Fila, db: Session) -> FilaOut:
    """Monta resposta com nome do paciente e CPF mascarado."""
    p = db.query(Paciente).filter(Paciente.id == f.paciente_id).first()
    pr = db.query(Profissional).filter(Profissional.id == f.profissional_id).first() if f.profissional_id else None
    return FilaOut(
        id=f.id,
        posicao=f.posicao,
        prioridade=f.prioridade,
        status=f.status,
        tempo_espera_estimado_min=f.tempo_espera_estimado_min,
        entrada=f.entrada,
        paciente_nome=p.nome if p else "",
        cpf_mascarado=mascarar_cpf(p.cpf) if p else None,
        profissional_nome=pr.nome if pr else None,
    )


@router.get("", response_model=List[FilaOut])
def listar(db: Session = Depends(get_db)):
    """Lista fila ordenada (público — não exige login)."""
    itens = listar_fila_ordenada(db)
    return [_to_out(f, db) for f in itens]


@router.post("/entrar", response_model=FilaOut, status_code=201)
async def entrar(
    data: FilaEntrada,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    """Paciente entra na fila; ML estima tempo de espera."""
    paciente = db.query(Paciente).filter(Paciente.id == data.paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")

    ja_na_fila = db.query(Fila).filter(
        Fila.paciente_id == data.paciente_id,
        Fila.status.in_([StatusFila.aguardando, StatusFila.chamado]),
    ).first()
    if ja_na_fila:
        raise HTTPException(status_code=400, detail="Paciente já está na fila")

    prioridade = data.prioridade
    if prioridade.value == "normal":
        prioridade = calcular_idade_prioridade(paciente)

    esp = "Clínico Geral"
    if data.profissional_id:
        pr = db.query(Profissional).filter(Profissional.id == data.profissional_id).first()
        if pr:
            esp = pr.especialidade

    tam = tamanho_fila(db) + 1
    tempo_est = ml_service.prever_tempo_espera(prioridade.value, esp, tam)

    fila = Fila(
        paciente_id=data.paciente_id,
        profissional_id=data.profissional_id,
        agendamento_id=data.agendamento_id,
        posicao=proxima_posicao(db),
        prioridade=prioridade,
        tempo_espera_estimado_min=tempo_est,
    )
    db.add(fila)
    if data.agendamento_id:
        ag = db.query(Agendamento).filter(Agendamento.id == data.agendamento_id).first()
        if ag:
            ag.status = StatusAgendamento.confirmado
    db.commit()
    db.refresh(fila)
    await registrar_log(user.id, "ENTRAR_FILA", "fila", fila.id)
    return _to_out(fila, db)


@router.post("/chamar-proximo", response_model=FilaOut)
async def chamar_proximo(
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    """Chama o próximo da fila respeitando prioridades."""
    itens = listar_fila_ordenada(db)
    aguardando = [f for f in itens if f.status == StatusFila.aguardando]
    if not aguardando:
        raise HTTPException(status_code=404, detail="Nenhum paciente aguardando na fila")
    fila = aguardando[0]
    fila.status = StatusFila.chamado
    fila.chamado_em = datetime.utcnow()
    db.commit()
    db.refresh(fila)
    await registrar_log(user.id, "CHAMAR_FILA", "fila", fila.id)
    return _to_out(fila, db)


@router.patch("/{fila_id}/finalizar")
async def finalizar(
    fila_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    """Marca atendimento na fila como concluído e grava histórico no MongoDB."""
    fila = db.query(Fila).filter(Fila.id == fila_id).first()
    if not fila:
        raise HTTPException(status_code=404)
    fila.status = StatusFila.finalizado
    fila.finalizado_em = datetime.utcnow()
    if fila.chamado_em:
        tempo_real = int((fila.finalizado_em - fila.entrada).total_seconds() / 60)
        pr = db.query(Profissional).filter(Profissional.id == fila.profissional_id).first()
        await registrar_historico_fila({
            "fila_id": fila.id,
            "paciente_id": fila.paciente_id,
            "prioridade": fila.prioridade.value,
            "tempo_espera_real_min": tempo_real,
            "dia_semana": fila.entrada.weekday(),
            "hora_entrada": fila.entrada.hour,
            "profissional_especialidade": pr.especialidade if pr else "Clínico Geral",
        })
    db.commit()
    return {"ok": True}
