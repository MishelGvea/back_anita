from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Usuario
from ..schemas import UsuarioRegistro, UsuarioLogin, UsuarioRespuesta, Token
from ..auth_utils import hash_contrasena, verificar_contrasena, crear_token

router = APIRouter()

@router.post("/registro", response_model=UsuarioRespuesta, status_code=status.HTTP_201_CREATED)
def registrar_usuario(datos: UsuarioRegistro, db: Session = Depends(get_db)):
    """Registrar un nuevo usuario"""
    
    # Verificar si el usuario ya existe
    usuario_existente = db.query(Usuario).filter(Usuario.usuario == datos.usuario).first()
    if usuario_existente:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso")
    
    # Verificar si el email ya existe
    email_existente = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if email_existente:
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

@router.post("/login", response_model=Token)
def iniciar_sesion(datos: UsuarioLogin, db: Session = Depends(get_db)):
    """Iniciar sesión"""
    
    # Buscar usuario
    usuario = db.query(Usuario).filter(Usuario.usuario == datos.usuario).first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos"
        )
    
    # Verificar contraseña
    if not verificar_contrasena(datos.contrasena, usuario.contrasena):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos"
        )
    
    # Crear token
    access_token = crear_token(data={"sub": usuario.usuario})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "usuario": usuario
    }

@router.get("/usuarios", response_model=list[UsuarioRespuesta])
def obtener_usuarios(db: Session = Depends(get_db)):
    """Obtener todos los usuarios (solo para pruebas)"""
    usuarios = db.query(Usuario).all()
    return usuarios