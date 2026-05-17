# main.py — ponto de entrada da API FastAPI

from contextlib import asynccontextmanager  # Gerencia startup/shutdown
from fastapi import FastAPI  # Framework web
from fastapi.middleware.cors import CORSMiddleware  # Permite chamadas de outros domínios
from fastapi.responses import HTMLResponse  # Página inicial simples

from .core.config import settings
from .core.database import connect_mongo, close_mongo
from .init_db import init_database
from .routers import auth, pacientes, agendamentos, fila, atendimentos, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Executado ao subir e ao desligar o servidor."""
    await connect_mongo()  # Conecta MongoDB (logs)
    init_database()  # Cria tabelas SQLite e dados demo
    yield
    await close_mongo()


app = FastAPI(
    title=settings.APP_NAME,
    description="Prontuário Eletrônico + Agendamento + Fila Inteligente para Clínicas Populares",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra cada módulo de rotas sob o prefixo /api
app.include_router(auth.router, prefix="/api")
app.include_router(pacientes.router, prefix="/api")
app.include_router(agendamentos.router, prefix="/api")
app.include_router(fila.router, prefix="/api")
app.include_router(atendimentos.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home():
    """Página inicial com instruções de teste."""
    return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Clínica Popular — API</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 640px; margin: 3rem auto; padding: 0 1rem; line-height: 1.5; }
    a { color: #0d6efd; }
    code { background: #f4f4f4; padding: 2px 6px; border-radius: 4px; }
    .ok { color: #198754; font-weight: 600; }
  </style>
</head>
<body>
  <h1>Clínica Popular — API</h1>
  <p class="ok">Servidor no ar (SQLite + MongoDB).</p>
  <p><strong>Como testar:</strong></p>
  <ol>
    <li>Abra <a href="/docs">/docs</a> (Swagger)</li>
    <li><code>POST /api/auth/login</code> → Try it out → body JSON com email e senha</li>
    <li>Copie o <code>access_token</code></li>
    <li>Clique em <strong>Authorize</strong> → cole <strong>só o token</strong> → Authorize</li>
    <li>Teste <code>GET /api/pacientes</code>, <code>GET /api/fila</code>, etc.</li>
  </ol>
  <p><a href="/api/health">Health</a> · <a href="/docs">Swagger</a></p>
</body>
</html>"""


@app.get("/api/health")
def health():
    """Verifica se a API está respondendo."""
    return {"status": "ok", "app": settings.APP_NAME, "database": "sqlite"}
