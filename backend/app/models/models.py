# models.py — tabelas do banco SQLite 

import enum
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Text,
    ForeignKey, Numeric, Enum as SAEnum,
)
from sqlalchemy.orm import relationship
from ..core.database import Base


# --- Enums (valores fixos gravados como texto no SQLite) ---

class PerfilUsuario(str, enum.Enum):
    admin = "admin"
    medico = "medico"
    recepcao = "recepcao"


class StatusAgendamento(str, enum.Enum):
    agendado = "agendado"
    confirmado = "confirmado"
    cancelado = "cancelado"
    faltou = "faltou"
    concluido = "concluido"


class StatusAtendimento(str, enum.Enum):
    em_andamento = "em_andamento"
    finalizado = "finalizado"
    cancelado = "cancelado"


class PrioridadeFila(str, enum.Enum):
    emergencia = "emergencia"
    gestante = "gestante"
    idoso = "idoso"
    pcd = "pcd"
    normal = "normal"


class StatusFila(str, enum.Enum):
    aguardando = "aguardando"
    chamado = "chamado"
    em_atendimento = "em_atendimento"
    finalizado = "finalizado"
    desistiu = "desistiu"


class Usuario(Base):
    """Usuários do sistema (login JWT)."""
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True)
    nome = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    perfil = Column(SAEnum(PerfilUsuario), default=PerfilUsuario.recepcao)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)


class Paciente(Base):
    """Cadastro de pacientes (prontuário)."""
    __tablename__ = "pacientes"
    id = Column(Integer, primary_key=True)
    nome = Column(String(200), nullable=False)
    cpf = Column(String(14), unique=True, nullable=False)
    cartao_sus = Column(String(20))
    data_nascimento = Column(Date, nullable=False)
    telefone = Column(String(20))
    endereco = Column(Text)
    prioritario = Column(Boolean, default=False)
    criado_em = Column(DateTime, default=datetime.utcnow)
    agendamentos = relationship("Agendamento", back_populates="paciente")
    atendimentos = relationship("Atendimento", back_populates="paciente")


class Profissional(Base):
    """Médicos e enfermeiros."""
    __tablename__ = "profissionais"
    id = Column(Integer, primary_key=True)
    nome = Column(String(200), nullable=False)
    crm_coren = Column(String(30), unique=True, nullable=False)
    especialidade = Column(String(100), nullable=False)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)


class Agendamento(Base):
    """Consultas agendadas com predição de no-show."""
    __tablename__ = "agendamentos"
    id = Column(Integer, primary_key=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)
    profissional_id = Column(Integer, ForeignKey("profissionais.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    data_hora = Column(DateTime, nullable=False)
    status = Column(SAEnum(StatusAgendamento), default=StatusAgendamento.agendado)
    prob_noshow = Column(Numeric(5, 4), default=0)
    observacoes = Column(Text)
    criado_em = Column(DateTime, default=datetime.utcnow)
    paciente = relationship("Paciente", back_populates="agendamentos")
    profissional = relationship("Profissional")


class Atendimento(Base):
    """Consulta em andamento ou finalizada."""
    __tablename__ = "atendimentos"
    id = Column(Integer, primary_key=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)
    profissional_id = Column(Integer, ForeignKey("profissionais.id"), nullable=False)
    agendamento_id = Column(Integer, ForeignKey("agendamentos.id"))
    inicio = Column(DateTime, default=datetime.utcnow)
    fim = Column(DateTime)
    status = Column(SAEnum(StatusAtendimento), default=StatusAtendimento.em_andamento)
    paciente = relationship("Paciente", back_populates="atendimentos")
    profissional = relationship("Profissional")
    anotacoes = relationship("AnotacaoMedica", back_populates="atendimento")


class AnotacaoMedica(Base):
    """Registros do prontuário (evolução, CID-10)."""
    __tablename__ = "anotacoes_medicas"
    id = Column(Integer, primary_key=True)
    atendimento_id = Column(Integer, ForeignKey("atendimentos.id", ondelete="CASCADE"))
    profissional_id = Column(Integer, ForeignKey("profissionais.id"))
    queixa_principal = Column(Text)
    evolucao = Column(Text, nullable=False)
    prescricao = Column(Text)
    cid10 = Column(String(10))
    criado_em = Column(DateTime, default=datetime.utcnow)
    atendimento = relationship("Atendimento", back_populates="anotacoes")


class Fila(Base):
    """Fila de espera com prioridade e tempo estimado (ML)."""
    __tablename__ = "fila"
    id = Column(Integer, primary_key=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)
    profissional_id = Column(Integer, ForeignKey("profissionais.id"))
    agendamento_id = Column(Integer, ForeignKey("agendamentos.id"))
    posicao = Column(Integer, nullable=False)
    prioridade = Column(SAEnum(PrioridadeFila), default=PrioridadeFila.normal)
    status = Column(SAEnum(StatusFila), default=StatusFila.aguardando)
    tempo_espera_estimado_min = Column(Integer, default=30)
    entrada = Column(DateTime, default=datetime.utcnow)
    chamado_em = Column(DateTime)
    finalizado_em = Column(DateTime)
    paciente = relationship("Paciente")
    profissional = relationship("Profissional")
