from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

class TwilioService:
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.phone_number = os.getenv("TWILIO_PHONE_NUMBER")
        self.client = Client(self.account_sid, self.auth_token)
    
    def enviar_sms(self, telefono_destino: str, mensaje: str):
        """Envía un SMS usando Twilio"""
        try:
            # Asegurarse que el número tenga formato internacional
            if not telefono_destino.startswith('+'):
                telefono_destino = f'+52{telefono_destino}'  # +52 para México
            
            message = self.client.messages.create(
                body=mensaje,
                from_=self.phone_number,
                to=telefono_destino
            )
            
            return {
                "success": True,
                "sid": message.sid,
                "status": message.status
            }
        except Exception as e:
            print(f"Error enviando SMS: {e}")
            return {
                "success": False,
                "error": str(e)
            }