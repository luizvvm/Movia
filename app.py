# app.py MODIFICADO
from flask import Flask, request, jsonify # Importamos o jsonify
# from twilio.twiml.messaging_response import MessagingResponse # Não precisamos mais disso
import config

# Importando nossos serviços e módulos (tudo igual aqui)
from services import gemini_service, database_service
from modules import routing_module, safety_module, sustainability_module
from modules.routing_module import formatar_lista_transportes, interpretar_escolha_transporte_nome
from modules.preferences_module import processar_preferencia

# Cria uma instância da aplicação Flask, que será o núcleo do servidor web.
app = Flask(__name__)

# --- FUNÇÕES DE LÓGICA (TUDO IGUAL ATÉ O FINAL) ---

# Função para detectar saudações
def is_saudacao(mensagem):
    mensagem = mensagem.lower()
    saudações = [
        'olá', 'ola', 'oi', 'hello', 'hi', 'eae', 'como vai', 'tudo bem',
        'olá movia', 'ola movia', 'oi movia', 'hello movia', 'hi movia',
        'bom dia', 'boa tarde', 'boa noite', 'saudações', 'hey', 'iae'
    ]
    return any(saudacao in mensagem for saudacao in saudações)

# Função para resposta de saudação
def get_saudacao_response():
    resposta = "🚍 *Olá! Eu sou a Movia, sua assistente de mobilidade inteligente!* 🤖\n\n"
    resposta += "Estou aqui para transformar seus deslocamentos no Rio de Janeiro em experiências mais práticas, seguras e sustentáveis! 🌟\n\n"
    resposta += "*Experimente perguntar por: *\n"
    resposta += "• 🚌 Encontrar rotas de ônibus, metrô, trem, VLT ou barca\n"
    resposta += "• 🗺️ Planejar seu trajeto de forma eficiente\n"
    resposta += "• ⏱️ Ver tempos de viagem e opções de transporte\n"
    resposta += "• 🛡️ Informações sobre segurança no trajeto\n"
    resposta += "• 🌱 Opções sustentáveis de mobilidade\n\n"
    resposta += "*Para começar, me diga:*\n"
    resposta += "• Seu ponto de partida 🏠\n" 
    resposta += "• Seu destino 🎯\n"
    resposta += "Sua privacidade é importante! Seus dados são usados apenas para melhorar sua experiência de mobilidade, em conformidade com a Lei Geral de Proteção de Dados."
    return resposta

# --- FIM DAS FUNÇÕES DE LÓGICA ---


# ROTA ANTIGA (PARA TWILIO) - VAMOS DESATIVÁ-LA POR ENQUANTO
# @app.route('/webhook/whatsapp', methods=['POST'])
# def webhook():
#     ... (todo o código antigo fica aqui comentado)


# 👇👇👇 NOSSA NOVA ROTA PARA O TESTE COM whatsapp-web.js 👇👇👇
@app.route('/process-message', methods=['POST'])
def process_message_from_bot():
    # 1. Recebe os dados em formato JSON do nosso script index.js
    data = request.get_json()
    message_body = data.get('message_body', '').strip()
    from_number = data.get('from_number', '')

    if not message_body or not from_number:
        return jsonify({'reply': ''})

    print(f"INFO: Mensagem recebida de {from_number} via Node.js: '{message_body}'")

    # 2. RODA EXATAMENTE A MESMA LÓGICA QUE VOCÊ JÁ TINHA!
    # 👇 VERIFICAÇÃO DE PREFERÊNCIAS PRIMEIRO
    preferencias = ['rápida', 'rápido', 'segura', 'seguro', 'econômica', 'econômico', 
                   'barata', 'barato', 'sustentável', 'acessível', 'todas']

    if any(pref in message_body.lower() for pref in preferencias):
        response_text = processar_preferencia(message_body, from_number)
        return jsonify({'reply': response_text})

    # Verificar se é uma saudação
    if is_saudacao(message_body):
        response_text = get_saudacao_response()
        database_service.registrar_interacao(from_number, message_body, 'saudacao')
        return jsonify({'reply': response_text})

    # Carregar resumo + últimas interações
    resumo = database_service.carregar_resumo_usuario(from_number)
    historico = database_service.carregar_interacoes_usuario(from_number, limit=5)
    contexto_interacoes = "\n".join([f"Usuário: {h['mensagem']} (intent: {h['intent']})" for h in historico])
    contexto = f"Histórico resumido: {resumo}\nÚltimas interações:\n{contexto_interacoes}\nNova mensagem: {message_body}"

    # Chamar IA
    intent_data = gemini_service.get_intent(contexto)
    intent = intent_data.get('intent', 'conversa_geral')
    parameters = intent_data.get('parameters', {})
    novo_resumo = intent_data.get('novo_resumo', resumo)

    # Registrar e Atualizar
    database_service.registrar_interacao(from_number, message_body, intent)
    database_service.atualizar_resumo_usuario(from_number, novo_resumo)

    # Roteamento normal
    if intent == 'consultar_rota':
        response_text = routing_module.handle_request(parameters, frase_usuario=message_body)
    elif intent == 'consultar_seguranca':
        response_text = safety_module.handle_request(parameters)
    elif intent == 'consultar_sustentabilidade':
        response_text = sustainability_module.handle_request(parameters)
    else:
        # Fallback se a IA não retornar uma resposta clara
        response_text = gemini_service.get_general_response(contexto) # Supondo que você tenha ou crie essa função

    # 3. Retorna a resposta em formato JSON para o script index.js
    return jsonify({'reply': response_text})


if __name__ == '__main__':
    # O Flask vai rodar na porta 5000, como definido no index.js
    app.run(debug=True, port=config.PORT or 5000)