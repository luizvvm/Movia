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
def webhook():
    message_body = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '')

    if not message_body or not from_number:
        return '', 204  

    print(f"INFO: Mensagem recebida de {from_number}: '{message_body}'")

    # 1. Carregar resumo + últimas interações
    resumo = database_service.carregar_resumo_usuario(from_number)
    historico = database_service.carregar_interacoes_usuario(from_number, limit=5)

    contexto_interacoes = "\n".join([
        f"Usuário: {h['mensagem']} (intent: {h['intent']})"
        for h in historico
    ])

    contexto = f"""
    Histórico resumido: {resumo}
    Últimas interações:
    {contexto_interacoes}
    Nova mensagem: {message_body}
    """

    # 2. Chamar IA (intenção + resumo no mesmo retorno)
    intent_data = gemini_service.get_intent(contexto)
    intent = intent_data.get('intent', 'conversa_geral')
    parameters = intent_data.get('parameters', {})
    novo_resumo = intent_data.get('novo_resumo', resumo)

    # 3. Registrar interação no banco
    database_service.registrar_interacao(from_number, message_body, intent)

    # 4. Atualizar resumo
    database_service.atualizar_resumo_usuario(from_number, novo_resumo)

    # 5. Roteamento normal
    if intent == 'consultar_rota':
        response_text = routing_module.handle_request(parameters)
    elif intent == 'consultar_seguranca':
        response_text = safety_module.handle_request(parameters)
    elif intent == 'consultar_sustentabilidade':
        response_text = sustainability_module.handle_request(parameters)
    else:
        response_text = "Olá! Sou a Mob.IA, sua assistente de mobilidade no Rio. Como posso te ajudar a se locomover hoje?"

    # 6. Construir TwiML
    twiml_response = MessagingResponse()
    twiml_response.message(response_text)

    return str(twiml_response)
if __name__ == '__main__':
    app.run(debug=True, port=config.PORT)