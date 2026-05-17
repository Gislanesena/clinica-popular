-- Consultas SQL — Clínica Popular

-- 1. Pacientes cadastrados hoje
SELECT id, nome, cpf, telefone, criado_em
FROM pacientes
WHERE criado_em::date = CURRENT_DATE
ORDER BY nome;

-- 2. Agenda do profissional em uma data
SELECT
    a.id,
    a.data_hora,
    a.status,
    a.prob_noshow,
    p.nome AS paciente,
    p.telefone
FROM agendamentos a
JOIN pacientes p ON p.id = a.paciente_id
WHERE a.profissional_id = :profissional_id
  AND a.data_hora::date = :data
  AND a.status NOT IN ('cancelado')
ORDER BY a.data_hora;

-- 3. Verificar conflito de horário (usado antes de inserir)
SELECT COUNT(*) AS conflitos
FROM agendamentos
WHERE profissional_id = :profissional_id
  AND data_hora = :data_hora
  AND status NOT IN ('cancelado', 'faltou');

-- 4. Fila atual ordenada por prioridade
SELECT * FROM vw_fila_ordenada;

-- 5. Histórico de consultas do paciente (prontuário)
SELECT
    at.id AS atendimento_id,
    at.inicio,
    at.fim,
    pr.nome AS medico,
    pr.especialidade,
    am.queixa_principal,
    am.evolucao,
    am.prescricao,
    am.cid10
FROM atendimentos at
JOIN profissionais pr ON pr.id = at.profissional_id
LEFT JOIN anotacoes_medicas am ON am.atendimento_id = at.id
WHERE at.paciente_id = :paciente_id
ORDER BY at.inicio DESC;

-- 6. Taxa de faltas por mês
SELECT
    DATE_TRUNC('month', data_hora) AS mes,
    COUNT(*) FILTER (WHERE status = 'faltou') AS faltas,
    COUNT(*) AS total,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'faltou') / NULLIF(COUNT(*), 0), 2) AS taxa_falta_pct
FROM agendamentos
WHERE data_hora >= CURRENT_DATE - INTERVAL '6 months'
GROUP BY 1
ORDER BY 1;

-- 7. Tempo médio real de espera (para treinar ML)
SELECT
  pr.especialidade,
  EXTRACT(DOW FROM f.entrada) AS dia_semana,
  EXTRACT(HOUR FROM f.entrada) AS hora,
  f.prioridade,
  AVG(EXTRACT(EPOCH FROM (f.chamado_em - f.entrada)) / 60) AS tempo_medio_min
FROM fila f
JOIN profissionais pr ON pr.id = f.profissional_id
WHERE f.chamado_em IS NOT NULL
GROUP BY 1, 2, 3, 4;

-- 8. Próximo da fila (prioridade)
SELECT f.*
FROM fila f
WHERE f.status = 'aguardando'
ORDER BY
    CASE f.prioridade
        WHEN 'emergencia' THEN 1 WHEN 'gestante' THEN 2
        WHEN 'idoso' THEN 3 WHEN 'pcd' THEN 4 ELSE 5
    END,
    f.posicao
LIMIT 1;

-- 9. Indicadores da clínica (dashboard)
SELECT
    (SELECT COUNT(*) FROM pacientes) AS total_pacientes,
    (SELECT COUNT(*) FROM agendamentos WHERE data_hora::date = CURRENT_DATE) AS agendamentos_hoje,
    (SELECT COUNT(*) FROM fila WHERE status = 'aguardando') AS na_fila_agora,
    (SELECT COUNT(*) FROM atendimentos WHERE inicio::date = CURRENT_DATE AND status = 'finalizado') AS atendidos_hoje;

-- 10. Pacientes com alto risco de falta hoje
SELECT a.id, p.nome, a.data_hora, a.prob_noshow
FROM agendamentos a
JOIN pacientes p ON p.id = a.paciente_id
WHERE a.data_hora::date = CURRENT_DATE
  AND a.prob_noshow > 0.6
  AND a.status IN ('agendado', 'confirmado')
ORDER BY a.prob_noshow DESC;
