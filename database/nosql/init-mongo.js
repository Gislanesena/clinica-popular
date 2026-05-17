// MongoDB — Logs e histórico para ML
db = db.getSiblingDB('clinica_popular');

db.createCollection('audit_logs');
db.createCollection('historico_fila');
db.createCollection('eventos_agendamento');

db.audit_logs.createIndex({ timestamp: -1 });
db.audit_logs.createIndex({ usuario_id: 1 });
db.audit_logs.createIndex({ acao: 1 });

db.historico_fila.createIndex({ fila_id: 1 });
db.historico_fila.createIndex({ timestamp: -1 });

// Dados de exemplo
db.audit_logs.insertMany([
  {
    usuario_id: 3,
    acao: 'LOGIN',
    entidade: 'usuarios',
    entidade_id: 3,
    payload_resumo: { email: 'recepcao@clinica.local' },
    ip: '127.0.0.1',
    timestamp: new Date()
  },
  {
    usuario_id: 3,
    acao: 'CREATE_PACIENTE',
    entidade: 'pacientes',
    entidade_id: 1,
    payload_resumo: { nome: 'José da Silva' },
    ip: '127.0.0.1',
    timestamp: new Date()
  }
]);

db.historico_fila.insertMany([
  {
    fila_id: 1,
    paciente_id: 1,
    prioridade: 'idoso',
    tempo_espera_real_min: 25,
    dia_semana: 1,
    hora_entrada: 9,
    profissional_especialidade: 'Clínico Geral',
    timestamp: new Date()
  },
  {
    fila_id: 2,
    paciente_id: 2,
    prioridade: 'normal',
    tempo_espera_real_min: 52,
    dia_semana: 1,
    hora_entrada: 10,
    profissional_especialidade: 'Clínico Geral',
    timestamp: new Date()
  }
]);

print('MongoDB clinica_popular inicializado.');
