from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..database import get_db
from ..models import Usuario
from ..auth_utils import (
    generar_secreto_totp, 
    generar_qr_totp, 
    verificar_codigo_totp
    # ← Eliminar verificar_token (no existe y no se usa)
)

router = APIRouter(prefix="/api/totp", tags=["TOTP"])

class HabilitarTOTPRequest(BaseModel):
    email: str

class VerificarTOTPRequest(BaseModel):
    email: str
    codigo: str

class HabilitarTOTPResponse(BaseModel):
    secreto: str
    qr_code: str
    mensaje: str

@router.post("/habilitar", response_model=HabilitarTOTPResponse)
async def habilitar_totp(
    request: HabilitarTOTPRequest,
    db: Session = Depends(get_db)
):
    """
    Genera un secreto TOTP y código QR para el usuario.
    El usuario debe escanear el QR con su app de autenticación.
    """
    # Buscar usuario
    usuario = db.query(Usuario).filter(Usuario.email == request.email).first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Generar secreto TOTP
    secreto = generar_secreto_totp()
    
    # Guardar secreto (pero no habilitar aún)
    usuario.secreto_totp = secreto
    usuario.totp_habilitado = False  # Se habilitará después de verificar
    db.commit()
    
    # Generar QR
    qr_code = generar_qr_totp(usuario.email, secreto)
    
    return {
        "secreto": secreto,
        "qr_code": qr_code,
        "mensaje": "Escanea el código QR con tu app de autenticación y luego verifica el código"
    }

@router.post("/verificar")
async def verificar_y_activar_totp(
    request: VerificarTOTPRequest,
    db: Session = Depends(get_db)
):
    """
    Verifica el código TOTP y activa la autenticación de dos factores.
    """
    # Buscar usuario
    usuario = db.query(Usuario).filter(Usuario.email == request.email).first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    if not usuario.secreto_totp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Primero debes generar un código QR"
        )
    
    # Verificar código
    if not verificar_codigo_totp(usuario.secreto_totp, request.codigo):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código TOTP inválido"
        )
    
    # Activar TOTP
    usuario.totp_habilitado = True
    db.commit()
    
    return {
        "mensaje": "Autenticación de dos factores activada exitosamente",
        "totp_habilitado": True
    }

@router.post("/deshabilitar")
async def deshabilitar_totp(
    request: VerificarTOTPRequest,
    db: Session = Depends(get_db)
):
    """
    Desactiva TOTP después de verificar un código válido.
    """
    usuario = db.query(Usuario).filter(Usuario.email == request.email).first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    if not usuario.totp_habilitado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TOTP no está habilitado"
        )
    
    # Verificar código antes de deshabilitar
    if not verificar_codigo_totp(usuario.secreto_totp, request.codigo):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código TOTP inválido"
        )
    
    # Deshabilitar
    usuario.totp_habilitado = False
    usuario.secreto_totp = None
    db.commit()
    
    return {
        "mensaje": "Autenticación de dos factores desactivada",
        "totp_habilitado": False
    }

@router.get("/estado/{email}")
async def verificar_estado_totp(email: str, db: Session = Depends(get_db)):
    """
    Verifica si un usuario tiene TOTP habilitado.
    """
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    return {
        "email": usuario.email,
        "totp_habilitado": usuario.totp_habilitado
    }