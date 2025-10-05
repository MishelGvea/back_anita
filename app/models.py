from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from .database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    usuario = Column(String(50), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    contrasena = Column(String(500), nullable=False)
    telefono = Column(String(20), nullable=False)
    
    email_verificado = Column(Boolean, default=False)
    telefono_verificado = Column(Boolean, default=False)
    pregunta_seguridad = Column(String(500), nullable=True)
    respuesta_seguridad = Column(String(500), nullable=True)
    secreto_totp = Column(String(100), nullable=True)
    totp_habilitado = Column(Boolean, default=False)
    
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

class CodigoVerificacion(Base):
    __tablename__ = "codigos_verificacion"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, nullable=False)
    codigo = Column(String(10), nullable=False)
    tipo = Column(String(20), nullable=False)
    expira = Column(DateTime, nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)