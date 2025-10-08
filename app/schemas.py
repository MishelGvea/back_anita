from pydantic import BaseModel, EmailStr
from typing import Optional

from datetime import datetime

class UsuarioRegistro(BaseModel):
    usuario: str
    nombre: str
    apellidos: str
    email: EmailStr
    contrasena: str
    telefono: str
class LoginConTOTP(BaseModel):
    usuario: str
    contrasena: str
    codigo_totp: Optional[str] = None  # ← Nuevo campo opcional

class UsuarioLogin(BaseModel):
    usuario: str
    contrasena: str
class Token(BaseModel):
    access_token: str
    token_type: str
    usuario: Optional[dict] = None

class UsuarioRespuesta(BaseModel):
    id: int
    usuario: str
    nombre: str
    apellidos: str
    email: str
    telefono: str
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    usuario: UsuarioRespuesta

class LoginRespuesta(BaseModel):
    access_token: Optional[str] = None
    token_type: str = "bearer"
    usuario: Optional[dict] = None
    requiere_totp: bool = False  # ← Indica si necesita código
    mensaje: str