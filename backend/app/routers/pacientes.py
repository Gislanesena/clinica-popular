# pacientes.py — CRUD e histórico de pacientes

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..core.database import get_db
from ..core.security import get_current_user
from ..models.models import Paciente, Usuario, Atendimento, AnotacaoMedica
from ..schemas.schemas import PacienteCreate, PacienteOut
from ..services.audit_service import registrar_log

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])


@router.get("", response_model=List[PacienteOut])
def listar(
    q: str = "",
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    """Lista pacientes; parâmetro q busca por nome ou CPF."""
    query = db.query(Paciente)
    if q:
        query = query.filter(Paciente.nome.ilike(f"%{q}%") | Paciente.cpf.ilike(f"%{q}%"))
    return query.order_by(Paciente.nome).limit(100).all()


@router.post("", response_model=PacienteOut, status_code=201)
async def criar(
    data: PacienteCreate,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    """Cadastra novo paciente no SQLite."""
    if db.query(Paciente).filter(Paciente.cpf == data.cpf).first():
        raise HTTPException(status_code=400, detail="CPF já cadastrado")
    paciente = Paciente(**data.model_dump())
    db.add(paciente)
    db.commit()
    db.refresh(paciente)
    await registrar_log(user.id, "CREATE_PACIENTE", "pacientes", paciente.id, {"nome": paciente.nome})
    return paciente


@router.get("/{paciente_id}", response_model=PacienteOut)
def obter(paciente_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    p = db.query(Paciente).filter(Paciente.id == paciente_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")
    return p


@router.get("/{paciente_id}/historico")
def historico(paciente_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    """Prontuário: atendimentos e anotações médicas do paciente."""
    atendimentos = (
        db.query(Atendimento)
        .filter(Atendimento.paciente_id == paciente_id)
        .order_by(Atendimento.inicio.desc())
        .all()
    )
    result = []
    for at in atendimentos:
        notas = db.query(AnotacaoMedica).filter(AnotacaoMedica.atendimento_id == at.id).all()
        result.append({
            "atendimento_id": at.id,
            "inicio": at.inicio,
            "fim": at.fim,
            "medico": at.profissional.nome if at.profissional else None,
            "anotacoes": [
                {
                    "evolucao": n.evolucao,
                    "queixa": n.queixa_principal,
                    "prescricao": n.prescricao,
                    "cid10": n.cid10,
                    "data": n.criado_em,
                }
                for n in notas
            ],
        })
    return result
