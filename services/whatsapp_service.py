# services/whatsapp_service.py
from twilio.rest import Client
import config

try:
    client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
    print("INFO: Cliente da Twilio inicializado com sucesso!")
except Exception as e:
    print(f"ERRO CRÍTICO: Falha ao inicializar o cliente da Twilio. Verifique suas credenciais. Erro: {e}")
    client = None

def send_message(to_number, message_body):
    """
    Envia uma mensagem de WhatsApp para um número específico.
    """
    if not client:
        print("ERRO: Cliente da Twilio não está disponível para enviar mensagem.")
        return

    try:
        client.messages.create(
            from_=config.TWILIO_WHATSAPP_NUMBER,
            to=to_number,
            body=message_body
        )
        print(f"INFO: Mensagem enviada para {to_number}: '{message_body}'")
    except Exception as e:
        print(f"ERRO: Falha ao enviar mensagem via Twilio: {e}")