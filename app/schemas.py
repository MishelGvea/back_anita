from pydantic import BaseModel, EmailStr
from datetime import datetime

class UsuarioRegistro(BaseModel):
    usuario: str
    nombre: str
    apellidos: str
    email: EmailStr
    contrasena: str
    telefono: str

class UsuarioLogin(BaseModel):
    usuario: str
    contrasena: str

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