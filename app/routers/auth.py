from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Usuario
from ..schemas import UsuarioRegistro, UsuarioLogin, UsuarioRespuesta, Token, LoginConTOTP, LoginRespuesta
from ..auth_utils import hash_contrasena, verificar_contrasena, crear_token, verificar_codigo_totp

router = APIRouter()


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
# 🔑 LOGIN CON AUTENTICACIÓN 2FA (TOTP)
# ==========================================
@router.post("/login", response_model=LoginRespuesta)
def iniciar_sesion(datos: LoginConTOTP, db: Session = Depends(get_db)):
    """
    Iniciar sesión con soporte para autenticación de dos factores (TOTP).

    Flujo:
    1. Valida usuario y contraseña
    2. Si tiene TOTP habilitado y no envió código → pedirlo
    3. Si tiene TOTP habilitado y envió código → verificarlo
    4. Si todo OK → devolver token JWT
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

    # 3️⃣ Verificar si tiene TOTP habilitado
    if usuario.totp_habilitado:
        # Si no envió código TOTP → solicitarlo
        if not datos.codigo_totp:
            return LoginRespuesta(
                mensaje="Ingresa tu código de autenticación de dos factores",
                requiere_totp=True
            )

        # Verificar el código TOTP
        if not verificar_codigo_totp(usuario.secreto_totp, datos.codigo_totp):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Código de autenticación inválido o expirado"
            )

    # 4️⃣ Si no tiene TOTP, o ya lo validó → generar token
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
            "telefono_verificado": usuario.telefono_verificado,
            "totp_habilitado": usuario.totp_habilitado
        },
        requiere_totp=False,
        mensaje="Login exitoso"
    )


# ==========================================
# 👥 LISTAR USUARIOS (SOLO PRUEBA)
# ==========================================
@router.get("/usuarios", response_model=list[UsuarioRespuesta])
def obtener_usuarios(db: Session = Depends(get_db)):
    """Obtener todos los usuarios (solo para pruebas)"""
    return db.query(Usuario).all()
