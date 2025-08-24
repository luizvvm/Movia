# app.py
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse # <-- MUDANÇA IMPORTANTE
import config

# Importando nossos serviços e módulos
from services import gemini_service, database_service
from modules import routing_module, safety_module, sustainability_module
from modules.routing_module import formatar_lista_transportes, interpretar_escolha_transporte

# Cria uma instância da aplicação Flask, que será o núcleo do servidor web.
app = Flask(__name__)

# Define a rota para o webhook do WhatsApp. Esta rota será o ponto de entrada para mensagens do WhatsApp
@app.route('/webhook/whatsapp', methods=['POST'])
# Função que processará todas as mensagens recebidas do WhatsApp.
def webhook():
    message_body = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '')  # Identificador do remetente

    if not message_body or not from_number:
        return '', 204 # Retorna uma resposta vazia se não houver corpo

    print(f"INFO: Mensagem recebida de {from_number}: '{message_body}'")

    # 1. Obter a intenção da IA
    intent_data = gemini_service.get_intent(message_body)
    intent = intent_data.get('intent', 'conversa_geral')
    parameters = intent_data.get('parameters', {})
    
    # 2. Registrar a interação no banco de dados
    database_service.registrar_interacao(from_number, message_body, intent)

    if intent == 'consultar_rota':
    # Verifica se é uma escolha de transporte
    if message_body.strip().isdigit():
        numero = int(message_body.strip())
        modo, tag = interpretar_escolha_transporte(numero)
        if modo:
            parameters['modo_transporte'] = modo
            response_text = routing_module.handle_request(parameters)
        else:
            response_text = "❌ Opção inválida. " + formatar_lista_transportes()
    else:
        # Processamento normal
        response_text = routing_module.handle_request(parameters)

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

    # 4. Construir a resposta no formato TwiML que a Twilio espera
    twiml_response = MessagingResponse()
    twiml_response.message(response_text)

    # Retorna a resposta formatada
    return str(twiml_response)

if __name__ == '__main__':
    app.run(debug=True, port=config.PORT)