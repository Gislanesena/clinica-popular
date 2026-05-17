-- Clínica Popular — Schema SQL de referência (documentação)
-- Em execução, as tabelas são criadas pelo SQLAlchemy no SQLite (init_db.py).
-- Este arquivo descreve a estrutura equivalente em SQL puro.
-- Prontuário Eletrônico + Agendamento + Fila Inteligente

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TYPE perfil_usuario AS ENUM ('admin', 'medico', 'recepcao');
CREATE TYPE status_agendamento AS ENUM ('agendado', 'confirmado', 'cancelado', 'faltou', 'concluido');
CREATE TYPE status_atendimento AS ENUM ('em_andamento', 'finalizado', 'cancelado');
CREATE TYPE prioridade_fila AS ENUM ('emergencia', 'gestante', 'idoso', 'pcd', 'normal');
CREATE TYPE status_fila AS ENUM ('aguardando', 'chamado', 'em_atendimento', 'finalizado', 'desistiu');

-- USUÁRIOS
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    perfil perfil_usuario NOT NULL DEFAULT 'recepcao',
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- PACIENTES
CREATE TABLE pacientes (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    cpf VARCHAR(14) NOT NULL UNIQUE,
    cartao_sus VARCHAR(20),
    data_nascimento DATE NOT NULL,
    telefone VARCHAR(20),
    endereco TEXT,
    prioritario BOOLEAN NOT NULL DEFAULT FALSE,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- PROFISSIONAIS
CREATE TABLE profissionais (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    crm_coren VARCHAR(30) NOT NULL UNIQUE,
    especialidade VARCHAR(100) NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- AGENDAMENTOS
CREATE TABLE agendamentos (
    id SERIAL PRIMARY KEY,
    paciente_id INTEGER NOT NULL REFERENCES pacientes(id),
    profissional_id INTEGER NOT NULL REFERENCES profissionais(id),
    usuario_id INTEGER REFERENCES usuarios(id),
    data_hora TIMESTAMP NOT NULL,
    status status_agendamento NOT NULL DEFAULT 'agendado',
    prob_noshow DECIMAL(5,4) DEFAULT 0,
    observacoes TEXT,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_agendamento_horario UNIQUE (profissional_id, data_hora)
);

-- ATENDIMENTOS
CREATE TABLE atendimentos (
    id SERIAL PRIMARY KEY,
    paciente_id INTEGER NOT NULL REFERENCES pacientes(id),
    profissional_id INTEGER NOT NULL REFERENCES profissionais(id),
    agendamento_id INTEGER REFERENCES agendamentos(id),
    inicio TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fim TIMESTAMP,
    status status_atendimento NOT NULL DEFAULT 'em_andamento'
);

-- ANOTAÇÕES MÉDICAS (Prontuário)
CREATE TABLE anotacoes_medicas (
    id SERIAL PRIMARY KEY,
    atendimento_id INTEGER NOT NULL REFERENCES atendimentos(id) ON DELETE CASCADE,
    profissional_id INTEGER NOT NULL REFERENCES profissionais(id),
    queixa_principal TEXT,
    evolucao TEXT NOT NULL,
    prescricao TEXT,
    cid10 VARCHAR(10),
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- FILA INTELIGENTE
CREATE TABLE fila (
    id SERIAL PRIMARY KEY,
    paciente_id INTEGER NOT NULL REFERENCES pacientes(id),
    profissional_id INTEGER REFERENCES profissionais(id),
    agendamento_id INTEGER REFERENCES agendamentos(id),
    posicao INTEGER NOT NULL,
    prioridade prioridade_fila NOT NULL DEFAULT 'normal',
    status status_fila NOT NULL DEFAULT 'aguardando',
    tempo_espera_estimado_min INTEGER DEFAULT 30,
    entrada TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    chamado_em TIMESTAMP,
    finalizado_em TIMESTAMP
);

-- Índices para performance
CREATE INDEX idx_agendamentos_data ON agendamentos(data_hora);
CREATE INDEX idx_agendamentos_paciente ON agendamentos(paciente_id);
CREATE INDEX idx_fila_status ON fila(status) WHERE status = 'aguardando';
CREATE INDEX idx_fila_prioridade ON fila(prioridade, posicao);
CREATE INDEX idx_atendimentos_paciente ON atendimentos(paciente_id);
CREATE INDEX idx_anotacoes_atendimento ON anotacoes_medicas(atendimento_id);

-- View: fila ordenada
CREATE OR REPLACE VIEW vw_fila_ordenada AS
SELECT
    f.id,
    f.posicao,
    f.prioridade,
    f.status,
    f.tempo_espera_estimado_min,
    f.entrada,
    p.id AS paciente_id,
    p.nome AS paciente_nome,
    LEFT(p.cpf, 3) || '.***.***-' || RIGHT(p.cpf, 2) AS cpf_mascarado,
    pr.nome AS profissional_nome,
    pr.especialidade
FROM fila f
JOIN pacientes p ON p.id = f.paciente_id
LEFT JOIN profissionais pr ON pr.id = f.profissional_id
WHERE f.status IN ('aguardando', 'chamado')
ORDER BY
    CASE f.prioridade
        WHEN 'emergencia' THEN 1
        WHEN 'gestante' THEN 2
        WHEN 'idoso' THEN 3
        WHEN 'pcd' THEN 4
        ELSE 5
    END,
    f.posicao;
