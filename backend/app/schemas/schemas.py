# schemas.py — validação de entrada/saída da API (Pydantic)

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field  # Modelos com validação automática
from ..models.models import (
    PerfilUsuario, StatusAgendamento, PrioridadeFila, StatusFila, StatusAtendimento
)


class Token(BaseModel):
    """Resposta do login com JWT."""
    access_token: str
    token_type: str = "bearer"
    perfil: str
    nome: str


class LoginRequest(BaseModel):
    """Corpo do POST /api/auth/login."""
    email: str
    senha: str


class UsuarioOut(BaseModel):
    """Dados públicos do usuário (sem senha)."""
    id: int
    nome: str
    email: str
    perfil: PerfilUsuario
    model_config = {"from_attributes": True}


class PacienteCreate(BaseModel):
    """Dados para cadastrar paciente."""
    nome: str = Field(..., min_length=3)
    cpf: str
    cartao_sus: Optional[str] = None
    data_nascimento: date
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    prioritario: bool = False


class PacienteOut(PacienteCreate):
    id: int
    criado_em: datetime
    model_config = {"from_attributes": True}


class ProfissionalOut(BaseModel):
    id: int
    nome: str
    crm_coren: str
    especialidade: str
    model_config = {"from_attributes": True}


class AgendamentoCreate(BaseModel):
    paciente_id: int
    profissional_id: int
    data_hora: datetime
    observacoes: Optional[str] = None


class AgendamentoOut(BaseModel):
    id: int
    paciente_id: int
    profissional_id: int
    data_hora: datetime
    status: StatusAgendamento
    prob_noshow: float
    observacoes: Optional[str]
    paciente_nome: Optional[str] = None
    model_config = {"from_attributes": True}


class FilaEntrada(BaseModel):
    """Paciente entrando na fila."""
    paciente_id: int
    profissional_id: Optional[int] = None
    agendamento_id: Optional[int] = None
    prioridade: PrioridadeFila = PrioridadeFila.normal


class FilaOut(BaseModel):
    """Item da fila para exibição (CPF mascarado)."""
    id: int
    posicao: int
    prioridade: PrioridadeFila
    status: StatusFila
    tempo_espera_estimado_min: int
    entrada: datetime
    paciente_nome: str
    cpf_mascarado: Optional[str] = None
    profissional_nome: Optional[str] = None
    model_config = {"from_attributes": True}


class AnotacaoCreate(BaseModel):
    atendimento_id: int
    profissional_id: int
    queixa_principal: Optional[str] = None
    evolucao: str
    prescricao: Optional[str] = None
    cid10: Optional[str] = None


class AnotacaoOut(AnotacaoCreate):
    id: int
    criado_em: datetime
    model_config = {"from_attributes": True}


class AtendimentoCreate(BaseModel):
    paciente_id: int
    profissional_id: int
    agendamento_id: Optional[int] = None
    fila_id: Optional[int] = None


class AtendimentoOut(BaseModel):
    id: int
    paciente_id: int
    profissional_id: int
    status: StatusAtendimento
    inicio: datetime
    model_config = {"from_attributes": True}


class DashboardOut(BaseModel):
    """Indicadores do painel."""
    total_pacientes: int
    agendamentos_hoje: int
    na_fila_agora: int
    atendidos_hoje: int
    tempo_medio_espera_min: float
    taxa_falta_pct: float


class PredicaoNoshowOut(BaseModel):
    agendamento_id: int
    prob_noshow: float
    risco: str
