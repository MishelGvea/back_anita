from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta 
from ..database import get_db
from ..models import Usuario
from ..schemas import UsuarioRegistro, UsuarioLogin, UsuarioRespuesta, Token, LoginConTOTP, LoginRespuesta
from ..auth_utils import hash_contrasena, verificar_contrasena, crear_token, verificar_codigo_totp
from ..models import CodigoVerificacion
from passlib.context import CryptContext

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ==========================================
# 🔐 REGISTRO DE USUARIO
# ==========================================
@router.post("/registro", response_model=UsuarioRespuesta, status_code=status.HTTP_201_CREATED)
def registrar_usuario(datos: UsuarioRegistro, db: Session = Depends(get_db)):
    """Registrar un nuevo usuario"""

    # Verificar si el usuario ya existe
    if db.query(Usuario).filter(Usuario.usuario == datos.usuario).first():
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso")

    # Verificar si el email ya existe
    if db.query(Usuario).filter(Usuario.email == datos.email).first():
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    # Crear nuevo usuario
    nuevo_usuario = Usuario(
        usuario=datos.usuario,
        nombre=datos.nombre,
        apellidos=datos.apellidos,
        email=datos.email,
        contrasena=hash_contrasena(datos.contrasena),
        telefono=datos.telefono
    )

    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    return nuevo_usuario


# ==========================================
# 🔑 LOGIN CON AUTENTICACIÓN 2FA (TOTP, EMAIL, PREGUNTA)
# ==========================================
@router.post("/login", response_model=LoginRespuesta)
def iniciar_sesion(datos: LoginConTOTP, db: Session = Depends(get_db)):
    """
    Iniciar sesión con soporte para autenticación de dos factores.

    Flujo:
    1. Valida usuario y contraseña
    2. Si tiene EMAIL verificado → pedir código
    3. Si tiene TOTP habilitado → pedir código
    4. Si tiene PREGUNTA configurada → pedir respuesta
    5. Si todo OK → devolver token JWT
    """

    # 1️⃣ Buscar usuario
    usuario = db.query(Usuario).filter(Usuario.usuario == datos.usuario).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos"
        )

    # 2️⃣ Verificar contraseña
    if not verificar_contrasena(datos.contrasena, usuario.contrasena):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos"
        )

    # ✅ Credenciales correctas

    # 3️⃣ ✨ Si eligió EMAIL (email_verificado = True)
    if usuario.email_verificado:
        if not datos.codigo_totp:
            from .verificacion import generar_codigo
            from .email import enviar_codigo_email
            
            codigo = generar_codigo()
            enviar_codigo_email(usuario.email, codigo, usuario.nombre)
            
            nuevo_codigo = CodigoVerificacion(
                usuario_id=usuario.id,
                codigo=codigo,
                tipo='email_login',
                expira=datetime.utcnow() + timedelta(minutes=10)
            )
            db.add(nuevo_codigo)
            db.commit()
            
            return LoginRespuesta(
                mensaje=f"📧 Código enviado a {usuario.email}",
                requiere_totp=True
            )
        
        codigo_valido = db.query(CodigoVerificacion).filter(
            CodigoVerificacion.usuario_id == usuario.id,
            CodigoVerificacion.codigo == datos.codigo_totp,
            CodigoVerificacion.tipo == 'email_login',
            CodigoVerificacion.expira > datetime.utcnow()
        ).first()
        
        if not codigo_valido:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Código inválido o expirado"
            )
        
        db.delete(codigo_valido)
        db.commit()


    # 3️⃣ Si tiene TOTP habilitado
    elif usuario.totp_habilitado:
        if not datos.codigo_totp:
            return LoginRespuesta(
                mensaje="🔐 Ingresa tu código de autenticación de dos factores",
                requiere_totp=True
            )

        # Verificar el código TOTP
        if not verificar_codigo_totp(usuario.secreto_totp, datos.codigo_totp):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Código de autenticación inválido o expirado"
            )

    # 3️⃣ ❓ Si tiene pregunta de seguridad configurada
    elif usuario.pregunta_seguridad and usuario.respuesta_seguridad:
        if not datos.codigo_totp:
            return LoginRespuesta(
                mensaje=f"❓ {usuario.pregunta_seguridad}",
                requiere_totp=True
            )
        
        # ✅ Verificar la respuesta ingresada
        respuesta_ingresada = datos.codigo_totp.lower().strip()
        # Truncar a 72 bytes igual que al guardar
        respuesta_truncada = respuesta_ingresada.encode('utf-8')[:72].decode('utf-8', errors='ignore')

        if not pwd_context.verify(respuesta_truncada, usuario.respuesta_seguridad):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Respuesta incorrecta"
            )

    # 4️⃣ Si no tiene ningún método, o ya lo validó → generar token
    access_token = crear_token(data={"sub": usuario.usuario})

    return LoginRespuesta(
        access_token=access_token,
        token_type="bearer",
        usuario={
            "id": usuario.id,
            "usuario": usuario.usuario,
            "nombre": usuario.nombre,
            "apellidos": usuario.apellidos,
            "email": usuario.email,
            "telefono": usuario.telefono,
            "email_verificado": usuario.email_verificado,
            "telefono_verificado": usuario.telefono_verificado,
            "totp_habilitado": usuario.totp_habilitado,
            "pregunta_seguridad": usuario.pregunta_seguridad
        },
        requiere_totp=False,
        mensaje="✅ Login exitoso"
    )


# ==========================================
# 👥 LISTAR USUARIOS (SOLO PRUEBA)
# ==========================================
@router.get("/usuarios", response_model=list[UsuarioRespuesta])
def obtener_usuarios(db: Session = Depends(get_db)):
    """Obtener todos los usuarios (solo para pruebas)"""
    return db.query(Usuario).all()