from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
import random
import string
import pyotp  # 👈 Import para Google Authenticator (TOTP)
from ..database import get_db
from ..models import Usuario, CodigoVerificacion
from .email import enviar_codigo_email
from passlib.context import CryptContext

router = APIRouter()

# ------------------------------------------------------
# 📱 MODELO DE VERIFICACIÓN POR SMS
# ------------------------------------------------------
class SolicitudCodigoSMS(BaseModel):
    usuario_id: int

class VerificarCodigoSMS(BaseModel):
    usuario_id: int
    codigo: str

def generar_codigo(longitud=6):
    """Genera un código numérico aleatorio"""
    return ''.join(random.choices(string.digits, k=longitud))

@router.post("/enviar-codigo-sms")
def enviar_codigo_sms(datos: SolicitudCodigoSMS, db: Session = Depends(get_db)):
    """Genera código de verificación (MODO PRUEBA - SIN ENVÍO REAL)"""
    
    usuario = db.query(Usuario).filter(Usuario.id == datos.usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if usuario.telefono_verificado:
        raise HTTPException(status_code=400, detail="El teléfono ya está verificado")
    
    # Generar código
    codigo = generar_codigo()
    
    # MODO PRUEBA: Solo imprimir en consola
    print(f"\n{'='*50}")
    print(f"📱 CÓDIGO DE VERIFICACIÓN SMS (MODO PRUEBA)")
    print(f"Teléfono: {usuario.telefono}")
    print(f"Código: {codigo}")
    print(f"Expira en: 10 minutos")
    print(f"{'='*50}\n")
    
    # Guardar código en BD
    nuevo_codigo = CodigoVerificacion(
        usuario_id=usuario.id,
        codigo=codigo,
        tipo='telefono',
        expira=datetime.utcnow() + timedelta(minutes=10)
    )
    
    db.add(nuevo_codigo)
    db.commit()
    
    return {
        "mensaje": f"Código enviado al número {usuario.telefono}",
        "codigo_prueba": codigo,  # Enviar código en respuesta (SOLO MODO PRUEBA)
        "modo_prueba": True
    }

@router.post("/verificar-codigo-sms")
def verificar_codigo_sms(datos: VerificarCodigoSMS, db: Session = Depends(get_db)):
    """Verifica el código SMS ingresado"""
    
    usuario = db.query(Usuario).filter(Usuario.id == datos.usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Buscar código válido
    codigo_valido = db.query(CodigoVerificacion).filter(
        CodigoVerificacion.usuario_id == datos.usuario_id,
        CodigoVerificacion.codigo == datos.codigo,
        CodigoVerificacion.tipo == 'telefono',
        CodigoVerificacion.expira > datetime.utcnow()
    ).first()
    
    if not codigo_valido:
        raise HTTPException(status_code=400, detail="Código inválido o expirado")
    
    # Marcar teléfono como verificado
    usuario.telefono_verificado = True
    db.commit()
    
    # Eliminar código usado
    db.delete(codigo_valido)
    db.commit()
    
    return {
        "mensaje": "Teléfono verificado exitosamente",
        "telefono_verificado": True
    }

# ------------------------------------------------------
# 🔐 VERIFICACIÓN POR TOTP (GOOGLE AUTHENTICATOR)
# ------------------------------------------------------

class GenerarTOTPRequest(BaseModel):
    usuario_id: int

class VerificarTOTPRequest(BaseModel):
    usuario_id: int
    codigo: str

@router.post("/generar-totp")
def generar_totp(datos: GenerarTOTPRequest, db: Session = Depends(get_db)):
    """Genera un código QR para configurar Google Authenticator"""
    usuario = db.query(Usuario).filter(Usuario.id == datos.usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Si el usuario no tiene secreto, se genera uno nuevo
    if not usuario.secreto_totp:
        usuario.secreto_totp = pyotp.random_base32()
        db.commit()
        db.refresh(usuario)

    # Generar URI para Google Authenticator
    totp = pyotp.TOTP(usuario.secreto_totp)
    provisioning_uri = totp.provisioning_uri(
        name=usuario.email,
        issuer_name="Sistema Auth"
    )

    print(f"🧩 URI de configuración TOTP: {provisioning_uri}")

    return {
        "mensaje": "Escanea el código QR con tu app autenticadora",
        "secreto": usuario.secreto_totp,
        "qr_uri": provisioning_uri
    }


@router.post("/verificar-totp")
def verificar_totp(datos: VerificarTOTPRequest, db: Session = Depends(get_db)):
    """Verifica el código TOTP ingresado"""
    usuario = db.query(Usuario).filter(Usuario.id == datos.usuario_id).first()
    if not usuario or not usuario.secreto_totp:
        raise HTTPException(status_code=404, detail="El usuario no tiene TOTP configurado")

    totp = pyotp.TOTP(usuario.secreto_totp)
    if not totp.verify(datos.codigo):
        raise HTTPException(status_code=400, detail="Código TOTP incorrecto o expirado")

    # Marcar TOTP como habilitado
    usuario.totp_habilitado = True
    db.commit()

    return {
        "mensaje": "TOTP verificado correctamente",
        "totp_habilitado": True
    }

# ------------------------------------------------------
# VERIFICACIÓN POR EMAIL (GMAIL)
# ------------------------------------------------------
class SolicitudCodigoEmail(BaseModel):
    usuario_id: int

class VerificarCodigoEmail(BaseModel):
    usuario_id: int
    codigo: str

@router.post("/enviar-codigo-email")
def enviar_codigo_gmail(datos: SolicitudCodigoEmail, db: Session = Depends(get_db)):
    """Genera y envía código de verificación por email"""
    
    usuario = db.query(Usuario).filter(Usuario.id == datos.usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if usuario.email_verificado:
        raise HTTPException(status_code=400, detail="El email ya está verificado")
    
    # Generar código de 6 dígitos
    codigo = generar_codigo()
    
    # Enviar email
    email_enviado = enviar_codigo_email(
        destinatario=usuario.email,
        codigo=codigo,
        nombre_usuario=usuario.nombre
    )
    
    if not email_enviado:
        raise HTTPException(
            status_code=500, 
            detail="Error al enviar el email. Verifica la configuración SMTP."
        )
    
    # Guardar código en BD
    nuevo_codigo = CodigoVerificacion(
        usuario_id=usuario.id,
        codigo=codigo,
        tipo='email',
        expira=datetime.utcnow() + timedelta(minutes=10)
    )
    
    db.add(nuevo_codigo)
    db.commit()
    
    print(f"\n{'='*50}")
    print(f"📧 CÓDIGO ENVIADO POR EMAIL")
    print(f"Destinatario: {usuario.email}")
    print(f"Código: {codigo}")
    print(f"Expira en: 10 minutos")
    print(f"{'='*50}\n")
    
    return {
        "mensaje": f"Código enviado a {usuario.email}",
        "email_enviado": True
    }

@router.post("/verificar-codigo-email")
def verificar_codigo_gmail(datos: VerificarCodigoEmail, db: Session = Depends(get_db)):
    """Verifica el código de email ingresado"""
    
    usuario = db.query(Usuario).filter(Usuario.id == datos.usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Buscar código válido
    codigo_valido = db.query(CodigoVerificacion).filter(
        CodigoVerificacion.usuario_id == datos.usuario_id,
        CodigoVerificacion.codigo == datos.codigo,
        CodigoVerificacion.tipo == 'email',
        CodigoVerificacion.expira > datetime.utcnow()
    ).first()
    
    if not codigo_valido:
        raise HTTPException(status_code=400, detail="Código inválido o expirado")
    
    # Marcar email como verificado
    usuario.email_verificado = True
    db.commit()
    
    # Eliminar código usado
    db.delete(codigo_valido)
    db.commit()
    
    return {
        "mensaje": "Email verificado exitosamente",
        "email_verificado": True
    }




pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class ConfigurarPreguntaRequest(BaseModel):
    usuario_id: int
    pregunta: str
    respuesta: str

class VerificarPreguntaRequest(BaseModel):
    usuario_id: int
    respuesta: str

@router.post("/configurar-pregunta")
def configurar_pregunta_seguridad(datos: ConfigurarPreguntaRequest, db: Session = Depends(get_db)):
    """Configura una pregunta de seguridad para el usuario"""
    
    usuario = db.query(Usuario).filter(Usuario.id == datos.usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if usuario.pregunta_seguridad:
        raise HTTPException(status_code=400, detail="Ya tienes una pregunta de seguridad configurada")
    
    # Validar que la pregunta no esté vacía
    if not datos.pregunta.strip() or not datos.respuesta.strip():
        raise HTTPException(status_code=400, detail="La pregunta y respuesta no pueden estar vacías")
    
    # ✅ DESPUÉS
    respuesta_preparada = datos.respuesta.lower().strip()
    # Truncar a 72 bytes para cumplir límite de bcrypt
    respuesta_truncada = respuesta_preparada.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    respuesta_hasheada = pwd_context.hash(respuesta_truncada)
    
    # Guardar pregunta y respuesta
    usuario.pregunta_seguridad = datos.pregunta.strip()
    usuario.respuesta_seguridad = respuesta_hasheada
    db.commit()
    
    return {
        "mensaje": "Pregunta de seguridad configurada exitosamente",
        "pregunta_configurada": True
    }

@router.get("/obtener-pregunta/{usuario_id}")
def obtener_pregunta_seguridad(usuario_id: int, db: Session = Depends(get_db)):
    """Obtiene la pregunta de seguridad del usuario (sin la respuesta)"""
    
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if not usuario.pregunta_seguridad:
        raise HTTPException(status_code=404, detail="No tienes pregunta de seguridad configurada")
    
    return {
        "pregunta": usuario.pregunta_seguridad,
        "tiene_pregunta": True
    }

@router.post("/verificar-pregunta")
def verificar_pregunta_seguridad(datos: VerificarPreguntaRequest, db: Session = Depends(get_db)):
    """Verifica la respuesta a la pregunta de seguridad"""
    
    usuario = db.query(Usuario).filter(Usuario.id == datos.usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if not usuario.pregunta_seguridad or not usuario.respuesta_seguridad:
        raise HTTPException(status_code=400, detail="No tienes pregunta de seguridad configurada")
    
    # Verificar respuesta (case-insensitive)
    respuesta_ingresada = datos.respuesta.lower().strip()
    
    if not pwd_context.verify(respuesta_ingresada, usuario.respuesta_seguridad):
        raise HTTPException(status_code=400, detail="Respuesta incorrecta")
    
    return {
        "mensaje": "Respuesta correcta. Pregunta verificada exitosamente",
        "verificada": True
    }