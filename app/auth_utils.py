from jose import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import pyotp
import qrcode
from io import BytesIO
import base64

load_dotenv()

# ==========================================
# ⚙️ CONFIGURACIÓN GLOBAL
# ==========================================
SECRET_KEY = os.getenv("SECRET_KEY", "clave-secreta-super-segura")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


# ==========================================
# 🔑 GESTIÓN DE CONTRASEÑAS
# ==========================================
# 🔸 Versión sin hashing (solo para pruebas)
def hash_contrasena(contrasena: str):
    """
    🚨 Versión temporal (sin hash)
    Solo devuelve la contraseña tal cual.
    """
    return contrasena


def verificar_contrasena(plain_password: str, hashed_password: str) -> bool:
    """
    Compara directamente texto plano.
    """
    return plain_password == hashed_password


# ==========================================
# 🧾 GENERACIÓN DE TOKENS JWT
# ==========================================
def crear_token(data: dict) -> str:
    """Genera un token JWT firmado con la clave secreta."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Alias para compatibilidad con otros archivos
crear_token_acceso = crear_token


# ==========================================
# 🔐 FUNCIONES TOTP (Google Authenticator)
# ==========================================
def generar_secreto_totp() -> str:
    """Genera un secreto aleatorio (base32) para usar con Google Authenticator."""
    return pyotp.random_base32()


def generar_qr_totp(email: str, secreto: str, emisor: str = "SEPT-Auth") -> str:
    """
    Genera un código QR en base64 para configurar TOTP en apps como Google Authenticator.
    
    Args:
        email (str): Correo del usuario que aparecerá en la app.
        secreto (str): Clave secreta TOTP.
        emisor (str): Nombre de tu sistema (Issuer).
        
    Returns:
        Imagen QR como data URI (data:image/png;base64,...)
    """
    # Crear URI TOTP estándar
    uri = pyotp.TOTP(secreto).provisioning_uri(name=email, issuer_name=emisor)

    # Crear código QR
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Convertir imagen QR a Base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    return f"data:image/png;base64,{img_str}"


def verificar_codigo_totp(secreto: str, codigo: str) -> bool:
    """
    Verifica si un código TOTP (de Google Authenticator) es válido.

    Args:
        secreto (str): Secreto TOTP del usuario.
        codigo (str): Código de 6 dígitos ingresado.

    Returns:
        bool: True si el código es válido, False si no.
    """
    totp = pyotp.TOTP(secreto)
    # valid_window=1 tolera ±30 segundos de desfase
    return totp.verify(codigo, valid_window=1)


def obtener_codigo_actual(secreto: str) -> str:
    """
    Devuelve el código TOTP actual (solo para pruebas).
    ⚠️ No usar en producción.
    """
    return pyotp.TOTP(secreto).now()
