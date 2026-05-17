# init_db.py — cria tabelas no SQLite e insere dados de demonstração

from datetime import date, datetime, timedelta
from .core.database import engine, Base, SessionLocal
from .core.security import hash_password
from .models.models import (
    Usuario, Paciente, Profissional, Agendamento, PerfilUsuario, StatusAgendamento
)


def init_database(db=None):
    """
    Cria todas as tabelas (se não existirem) e popula usuários/pacientes demo.
    Chamado automaticamente quando a API inicia.
    """
    Base.metadata.create_all(bind=engine)
    own_session = db is None
    db = db or SessionLocal()
    try:
        if db.query(Usuario).count() == 0:
            usuarios = [
                ("Administrador", "admin@clinica.local", "clinica123", PerfilUsuario.admin),
                ("Dr. João Silva", "medico@clinica.local", "clinica123", PerfilUsuario.medico),
                ("Maria Recepção", "recepcao@clinica.local", "clinica123", PerfilUsuario.recepcao),
            ]
            for nome, email, senha, perfil in usuarios:
                db.add(Usuario(
                    nome=nome, email=email,
                    senha_hash=hash_password(senha), perfil=perfil,
                ))
            db.commit()

        if db.query(Profissional).count() == 0:
            profs = [
                ("Dr. João Silva", "CRM-SP 123456", "Clínico Geral"),
                ("Dra. Ana Costa", "CRM-SP 654321", "Pediatria"),
                ("Enf. Carlos Lima", "COREN-SP 789012", "Enfermagem"),
            ]
            for nome, reg, esp in profs:
                db.add(Profissional(nome=nome, crm_coren=reg, especialidade=esp))
            db.commit()

        if db.query(Paciente).count() == 0:
            pacientes = [
                ("José da Silva", "123.456.789-00", "898001234567890", date(1955, 3, 15), True),
                ("Maria Oliveira", "987.654.321-00", "898009876543210", date(1990, 7, 22), False),
                ("Ana Souza", "456.789.123-00", "898004567891230", date(1988, 11, 30), False),
            ]
            for nome, cpf, sus, dn, pri in pacientes:
                db.add(Paciente(
                    nome=nome, cpf=cpf, cartao_sus=sus,
                    data_nascimento=dn, telefone="(11) 90000-0000",
                    endereco="Endereço exemplo", prioritario=pri,
                ))
            db.commit()

        if db.query(Agendamento).count() == 0:
            hoje = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
            db.add(Agendamento(
                paciente_id=1, profissional_id=1, usuario_id=3,
                data_hora=hoje, status=StatusAgendamento.confirmado, prob_noshow=0.15,
            ))
            db.add(Agendamento(
                paciente_id=2, profissional_id=1, usuario_id=3,
                data_hora=hoje + timedelta(minutes=30),
                status=StatusAgendamento.agendado, prob_noshow=0.45,
            ))
            db.commit()
    finally:
        if own_session:
            db.close()
