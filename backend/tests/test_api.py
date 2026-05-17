# test_api.py — testes automatizados da API

import pytest  # Framework de testes
from fastapi.testclient import TestClient  # Cliente HTTP simulado
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.core.database as db_module
from app.main import app
from app.core.database import Base, get_db
from app.init_db import init_database

# SQLite em memória para testes isolados
SQLITE_URL = "sqlite:///:memory:"


@pytest.fixture(autouse=True)
def setup_db(monkeypatch):
    """Substitui o banco real por um SQLite temporário antes de cada teste."""
    test_engine = create_engine(
        SQLITE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    TestingSession = sessionmaker(bind=test_engine)
    monkeypatch.setattr(db_module, "engine", test_engine)
    monkeypatch.setattr(db_module, "SessionLocal", TestingSession)
    Base.metadata.create_all(bind=test_engine)
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client(setup_db):
    """Cliente FastAPI com banco de teste e dados demo."""
    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    init_database(db=setup_db)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _login(client, email="recepcao@clinica.local", senha="clinica123"):
    """Helper: faz login e retorna o token JWT."""
    r = client.post("/api/auth/login", json={"email": email, "senha": senha})
    assert r.status_code == 200
    return r.json()["access_token"]


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_login_invalido(client):
    r = client.post("/api/auth/login", json={"email": "x@x.com", "senha": "errada"})
    assert r.status_code == 401


def test_criar_paciente(client):
    token = _login(client)
    r = client.post(
        "/api/pacientes",
        json={
            "nome": "Teste Silva",
            "cpf": "111.222.333-44",
            "data_nascimento": "1990-01-01",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    assert r.json()["nome"] == "Teste Silva"


def test_cpf_duplicado(client):
    token = _login(client)
    payload = {"nome": "A", "cpf": "999.888.777-66", "data_nascimento": "1980-05-05"}
    client.post("/api/pacientes", json=payload, headers={"Authorization": f"Bearer {token}"})
    r = client.post("/api/pacientes", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 400


def test_agendamento_conflito(client):
    token = _login(client)
    from datetime import datetime, timedelta
    dt = (datetime.now() + timedelta(days=1)).replace(hour=14, minute=0, second=0, microsecond=0)
    payload = {"paciente_id": 1, "profissional_id": 1, "data_hora": dt.isoformat()}
    h = {"Authorization": f"Bearer {token}"}
    r1 = client.post("/api/agendamentos", json=payload, headers=h)
    assert r1.status_code == 201
    r2 = client.post("/api/agendamentos", json=payload, headers=h)
    assert r2.status_code == 409


def test_fila_entrar(client):
    token = _login(client)
    r = client.post(
        "/api/fila/entrar",
        json={"paciente_id": 1, "profissional_id": 1, "prioridade": "normal"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    assert r.json()["tempo_espera_estimado_min"] >= 5


def test_fila_listar(client):
    token = _login(client)
    h = {"Authorization": f"Bearer {token}"}
    client.post("/api/fila/entrar", json={"paciente_id": 1, "prioridade": "idoso"}, headers=h)
    r = client.get("/api/fila")
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_rota_protegida_sem_token(client):
    r = client.get("/api/pacientes")
    assert r.status_code == 403  # HTTPBearer retorna 403 quando token ausente
