import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# ⚙️ Configuración del servidor SMTP (Gmail)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "tu_email@gmail.com")  # ← Cambiar por tu email
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "tu_app_password")  # ← Contraseña de aplicación de Gmail

def enviar_codigo_email(destinatario: str, codigo: str, nombre_usuario: str):
    """
    Envía un código de verificación por email usando Gmail SMTP
    
    Args:
        destinatario: Email del usuario
        codigo: Código de 6 dígitos
        nombre_usuario: Nombre del usuario
    
    Returns:
        bool: True si se envió correctamente, False si hubo error
    """
    try:
        # Crear mensaje
        mensaje = MIMEMultipart("alternative")
        mensaje["Subject"] = "🔐 Tu código de verificación"
        mensaje["From"] = SMTP_EMAIL
        mensaje["To"] = destinatario

        # Cuerpo del email en HTML
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h1 style="color: #4CAF50; text-align: center;">🔐 Código de Verificación</h1>
                    <p style="font-size: 16px; color: #333;">Hola <strong>{nombre_usuario}</strong>,</p>
                    <p style="font-size: 16px; color: #333;">Tu código de verificación es:</p>
                    
                    <div style="background-color: #f0f0f0; padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0;">
                        <h2 style="color: #4CAF50; font-size: 36px; letter-spacing: 8px; margin: 0;">{codigo}</h2>
                    </div>
                    
                    <p style="font-size: 14px; color: #666;">Este código expirará en <strong>10 minutos</strong>.</p>
                    <p style="font-size: 14px; color: #666;">Si no solicitaste este código, ignora este mensaje.</p>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                    <p style="font-size: 12px; color: #999; text-align: center;">Sistema de Autenticación Segura</p>
                </div>
            </body>
        </html>
        """

        # Adjuntar HTML al mensaje
        parte_html = MIMEText(html, "html")
        mensaje.attach(parte_html)

        # Conectar y enviar email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as servidor:
            servidor.starttls()  # Habilitar seguridad TLS
            servidor.login(SMTP_EMAIL, SMTP_PASSWORD)
            servidor.send_message(mensaje)
        
        print(f"✅ Email enviado exitosamente a {destinatario}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("❌ Error de autenticación: Verifica tu email y contraseña de aplicación")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ Error SMTP: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Error al enviar email: {str(e)}")
        return False