from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
import random
import string
from ..database import get_db
from ..models import Usuario, CodigoVerificacion

router = APIRouter()

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