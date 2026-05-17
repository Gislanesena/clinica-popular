-- Dados iniciais — senha padrão: clinica123 (bcrypt)
INSERT INTO usuarios (nome, email, senha_hash, perfil) VALUES
('Administrador', 'admin@clinica.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.G2o1qJqK5K5K5K', 'admin'),
('Dr. João Silva', 'medico@clinica.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.G2o1qJqK5K5K5K', 'medico'),
('Maria Recepção', 'recepcao@clinica.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.G2o1qJqK5K5K5K', 'recepcao');

INSERT INTO profissionais (nome, crm_coren, especialidade) VALUES
('Dr. João Silva', 'CRM-SP 123456', 'Clínico Geral'),
('Dra. Ana Costa', 'CRM-SP 654321', 'Pediatria'),
('Enf. Carlos Lima', 'COREN-SP 789012', 'Enfermagem');

INSERT INTO pacientes (nome, cpf, cartao_sus, data_nascimento, telefone, endereco, prioritario) VALUES
('José da Silva', '123.456.789-00', '898001234567890', '1955-03-15', '(11) 98765-4321', 'Rua das Flores, 100', TRUE),
('Maria Oliveira', '987.654.321-00', '898009876543210', '1990-07-22', '(11) 91234-5678', 'Av. Brasil, 500', FALSE),
('Ana Souza', '456.789.123-00', '898004567891230', '1988-11-30', '(11) 99876-5432', 'Rua Central, 45', FALSE);

-- Agendamentos de exemplo
INSERT INTO agendamentos (paciente_id, profissional_id, usuario_id, data_hora, status, prob_noshow) VALUES
(1, 1, 3, CURRENT_DATE + TIME '09:00', 'confirmado', 0.15),
(2, 1, 3, CURRENT_DATE + TIME '09:30', 'agendado', 0.45),
(3, 2, 3, CURRENT_DATE + TIME '10:00', 'agendado', 0.72);
