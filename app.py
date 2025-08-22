# app.py
from flask import Flask, request
import config

# Importando nossos serviços e módulos
from services import gemini_service, whatsapp_service, database_service
from modules import routing_module, safety_module, sustainability_module

app = Flask(__name__)

@app.route('/webhook/whatsapp', methods=['POST'])
def webhook():
    message_body = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '')

    if not message_body or not from_number:
        return 'OK', 200

    print(f"INFO: Mensagem recebida de {from_number}: '{message_body}'")

    # 1. Obter a intenção da IA
    intent_data = gemini_service.get_intent(message_body)
    intent = intent_data.get('intent', 'conversa_geral')
    parameters = intent_data.get('parameters', {})
    
    # 2. Registrar a interação no banco de dados
    database_service.registrar_interacao(from_number, message_body, intent)

    response_text = ""

    # 3. Roteamento para o módulo correto
    if intent == 'consultar_rota':
        response_text = routing_module.handle_request(parameters)
        
    elif intent == 'consultar_seguranca':
        response_text = safety_module.handle_request(parameters)
        
    elif intent == 'consultar_sustentabilidade':
        response_text = sustainability_module.handle_request(parameters)
        
    else: # conversa_geral ou qualquer outra coisa
        response_text = "Olá! Sou a Mob.IA, sua assistente de mobilidade no Rio. Como posso te ajudar a se locomover hoje? Você pode me perguntar sobre rotas, segurança ou opções de transporte sustentável."

    # 4. Enviar a resposta para o usuário
    whatsapp_service.send_message(from_number, response_text)

    return 'OK', 200

if __name__ == '__main__':
    app.run(debug=True, port=config.PORT)