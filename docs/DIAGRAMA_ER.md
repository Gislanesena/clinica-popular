# Diagrama Entidade-Relacionamento

## Modelo Conceitual

```mermaid
erDiagram
    USUARIOS ||--o{ AGENDAMENTOS : cria
    USUARIOS {
        int id PK
        string nome
        string email UK
        string senha_hash
        enum perfil
        boolean ativo
        timestamp criado_em
    }

    PACIENTES ||--o{ AGENDAMENTOS : possui
    PACIENTES ||--o{ ATENDIMENTOS : recebe
    PACIENTES ||--o{ FILA : entra
    PACIENTES {
        int id PK
        string nome
        string cpf UK
        string cartao_sus
        date data_nascimento
        string telefone
        string endereco
        boolean prioritario
        timestamp criado_em
    }

    PROFISSIONAIS ||--o{ AGENDAMENTOS : atende
    PROFISSIONAIS ||--o{ ATENDIMENTOS : realiza
    PROFISSIONAIS {
        int id PK
        string nome
        string crm_coren
        string especialidade
        boolean ativo
    }

    AGENDAMENTOS ||--o| ATENDIMENTOS : gera
    AGENDAMENTOS {
        int id PK
        int paciente_id FK
        int profissional_id FK
        int usuario_id FK
        timestamp data_hora
        enum status
        float prob_noshow
        text observacoes
    }

    ATENDIMENTOS ||--o{ ANOTACOES_MEDICAS : contem
    ATENDIMENTOS {
        int id PK
        int paciente_id FK
        int profissional_id FK
        int agendamento_id FK
        timestamp inicio
        timestamp fim
        enum status
    }

    ANOTACOES_MEDICAS {
        int id PK
        int atendimento_id FK
        int profissional_id FK
        text queixa_principal
        text evolucao
        text prescricao
        text cid10
        timestamp criado_em
    }

    FILA {
        int id PK
        int paciente_id FK
        int profissional_id FK
        int agendamento_id FK
        int posicao
        enum prioridade
        enum status
        int tempo_espera_estimado_min
        timestamp entrada
        timestamp chamado_em
    }
```

## Cardinalidades

| Relacionamento | Cardinalidade | Regra |
|----------------|---------------|-------|
| Paciente → Agendamento | 1:N | Um paciente pode ter vários agendamentos |
| Profissional → Agendamento | 1:N | Um profissional atende vários pacientes |
| Agendamento → Atendimento | 1:0..1 | Nem todo agendamento vira atendimento (falta) |
| Atendimento → Anotação | 1:N | Várias notas por atendimento (evoluções) |
| Paciente → Fila | 1:N | Histórico de passagens na fila |

## NoSQL (MongoDB) — Logs e Histórico

Coleção `audit_logs` (documentos flexíveis):

```json
{
  "_id": "ObjectId",
  "usuario_id": 1,
  "acao": "CREATE_PACIENTE",
  "entidade": "pacientes",
  "entidade_id": 42,
  "payload_resumo": { "nome": "Maria S." },
  "ip": "192.168.1.10",
  "timestamp": "2026-05-17T14:30:00Z"
}
```

Coleção `historico_fila` — snapshots para análise ML:

```json
{
  "fila_id": 15,
  "paciente_id": 8,
  "prioridade": "idoso",
  "tempo_espera_real_min": 47,
  "dia_semana": 1,
  "hora_entrada": 9,
  "profissional_especialidade": "Clínico Geral"
}
```
