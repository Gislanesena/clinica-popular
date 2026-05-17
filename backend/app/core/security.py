# security.py — senhas, tokens JWT e proteção das rotas

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt  # Cria e valida tokens JWT
from passlib.context import CryptContext  # Hash de senhas com bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials  # Auth no Swagger
from sqlalchemy.orm import Session
from .config import settings
from ..models.models import Usuario
from .database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# HTTPBearer: no Swagger, o botão Authorize pede só o token (não e-mail/senha)
bearer_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    """Gera hash bcrypt da senha (nunca salvar senha em texto puro)."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Compara senha digitada com o hash gravado no banco."""
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Gera JWT com id do usuário, perfil e data de expiração."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    """Lê o token do header Authorization e retorna o usuário logado."""
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = int(payload.get("sub"))
        if user_id is None:
            raise credentials_exception
    except (JWTError, ValueError):
        raise credentials_exception
    user = db.query(Usuario).filter(Usuario.id == user_id, Usuario.ativo == True).first()
    if not user:
        raise credentials_exception
    return user


def require_roles(*roles: str):
    """Decorator de dependência: restringe rota a perfis específicos."""
    async def checker(user: Usuario = Depends(get_current_user)) -> Usuario:
        if user.perfil.value not in roles and user.perfil.value != "admin":
            raise HTTPException(status_code=403, detail="Acesso negado para este perfil")
        return user
    return checker
