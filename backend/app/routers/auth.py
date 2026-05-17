# auth.py — login e dados do usuário autenticado

from fastapi import APIRouter, Depends, HTTPException  # Router e erros HTTP
from sqlalchemy.orm import Session  # Sessão do banco SQLite
from ..core.database import get_db
from ..core.security import verify_password, create_access_token, get_current_user
from ..models.models import Usuario
from ..schemas.schemas import LoginRequest, Token, UsuarioOut
from ..services.audit_service import registrar_log

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login", response_model=Token)
async def login(data: LoginRequest, db: Session = Depends(get_db)):
    """
    Login com JSON (use este endpoint no Swagger, não o botão Authorize).
    Body: {"email": "recepcao@clinica.local", "senha": "clinica123"}
    """
    user = db.query(Usuario).filter(Usuario.email == data.email, Usuario.ativo == True).first()
    if not user or not verify_password(data.senha, user.senha_hash):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    token = create_access_token({"sub": str(user.id), "perfil": user.perfil.value})
    await registrar_log(user.id, "LOGIN", "usuarios", user.id, {"email": user.email})
    return Token(
        access_token=token,
        perfil=user.perfil.value,
        nome=user.nome,
    )


@router.get("/me", response_model=UsuarioOut)
async def me(user: Usuario = Depends(get_current_user)):
    """Retorna dados do usuário logado (requer token no Authorize)."""
    return user
