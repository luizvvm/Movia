import requests
import os
from config import GOOGLE_MAPS_API_KEY

def gerar_lista_transportes_publicos():
    """
    Retorna lista numerada de transportes públicos do Rio (sem carro)
    """
    transportes = [
        {'numero': 1, 'emoji': '🚌', 'nome': 'Ônibus', 'modo': 'onibus', 'tag': 'bus'},
        {'numero': 2, 'emoji': '🚇', 'nome': 'Metrô', 'modo': 'metro', 'tag': 'subway'},
        {'numero': 3, 'emoji': '🚆', 'nome': 'Trem', 'modo': 'trem', 'tag': 'train'},
        {'numero': 4, 'emoji': '🚋', 'nome': 'VLT', 'modo': 'vlt', 'tag': 'tram'},
        {'numero': 5, 'emoji': '⛴️', 'nome': 'Barca', 'modo': 'barca', 'tag': 'ferry'},
        {'numero': 6, 'emoji': '🚴‍♂️', 'nome': 'Bicicleta', 'modo': 'bicicleta', 'tag': 'bicycling'},
        {'numero': 7, 'emoji': '🚶‍♂️', 'nome': 'Caminhada', 'modo': 'caminhada', 'tag': 'walking'}
    ]
    return transportes

def formatar_lista_transportes():
    """
    Formata a lista para display no WhatsApp
    """
    transportes = gerar_lista_transportes_publicos()
    
    mensagem = "🚍 *Como você prefere ir?*\n\n"
    
    for transp in transportes:
        mensagem += f"{transp['numero']}. {transp['emoji']} {transp['nome']}\n"
    
    mensagem += "\n*Digite o número da opção desejada:*"
    
    return mensagem

def interpretar_escolha_transporte(numero_escolhido):
    """
    Converte número escolhido em modo de transporte API
    """
    transportes = gerar_lista_transportes_publicos()
    
    for transp in transportes:
        if transp['numero'] == numero_escolhido:
            return transp['modo'], transp['tag']
    
    return None, None

def get_modo_transporte_por_tag(tag):
    """
    Retorna modo em português pela tag da API
    """
    modos = {
        'bus': 'ônibus',
        'subway': 'metrô', 
        'train': 'trem',
        'tram': 'VLT',
        'ferry': 'barca',
        'bicycling': 'bicicleta',
        'walking': 'caminhada'
    }
    return modos.get(tag, 'transporte')

def consultar_google_maps(origem, destino, modo_transporte="transit", api_key=None):
    """
    Consulta a Google Maps Directions API para rotas reais
    """
    url = "https://maps.googleapis.com/maps/api/directions/json"

    # Mapeamento completo dos transportes do Rio
    modos_api = {
        'onibus': 'transit',
        'ônibus': 'transit',
        'metro': 'transit', 
        'metrô': 'transit',
        'trem': 'transit',
        'vlt': 'transit',
        'barca': 'transit',
        'bicicleta': 'bicycling',
        'bike': 'bicycling',
        'caminhada': 'walking',
        'a pé': 'walking',
        'walking': 'walking',
        'bicycling': 'bicycling'
    }

    modo_api = modos_api.get(modo_transporte, "transit")

    origem_completa = f"{origem}, Rio de Janeiro, Brasil"
    destino_completo = f"{destino}, Rio de Janeiro, Brasil"

    params = {
        "origin": origem_completa,
        "destination": destino_completo,
        "mode": modo_api,
        "key": api_key,
        "language": "pt-BR",
        "region": "br"
    }

    # Configurações específicas para cada tipo de transporte público
    if modo_api == 'transit':
        # Define quais modos de transporte incluir baseado na escolha
        if modo_transporte == 'metro':
            params["transit_mode"] = "subway"
        elif modo_transporte == 'trem':
            params["transit_mode"] = "train"  
        elif modo_transporte == 'vlt':
            params["transit_mode"] = "tram"
        elif modo_transporte == 'barca':
            params["transit_mode"] = "ferry"
        elif modo_transporte in ['onibus', 'ônibus']:
            params["transit_mode"] = "bus"
        else:
            # Todos os modos públicos
            params["transit_mode"] = "bus|subway|train|tram|ferry"
            
        params["transit_routing_preference"] = "fewer_transfers"

    response = requests.get(url, params=params, timeout=10)
    return response.json()

def formatar_resposta_google_maps(data, origem, destino, modo):
    rota = data['routes'][0]
    perna = rota['legs'][0]
    
    # Extrai informações principais
    tempo_total = perna['duration']['text']
    distancia_total = perna['distance']['text']
    preco = rota['fare']['text'] if 'fare' in rota else 'R$ 4,30'
    
    # Constrói a resposta
    resposta = f"🚍 *ROTA ENCONTRADA!*\n\n"
    resposta += f"📍 *De:* {origem.title()}\n"
    resposta += f"🎯 *Para:* {destino.title()}\n"
    resposta += f"⏰ *Tempo:* {tempo_total}\n"
    resposta += f"📏 *Distância:* {distancia_total}\n"
    resposta += f"💵 *Preço:* {preco}\n\n"
    
    resposta += "📋 *Instruções:*\n"
    
    # Processa cada etapa da viagem
    for i, etapa in enumerate(perna['steps'], 1):
        instrucao = etapa['html_instructions']
        
        # Limpa tags HTML
        instrucao = instrucao.replace('<b>', '').replace('</b>', '')
        instrucao = instrucao.replace('<div style="font-size:0.9em">', ' (')
        instrucao = instrucao.replace('</div>', ')')
        
        # Adiciona emoji baseado no modo
        if 'transit_details' in etapa:
            detalhes = etapa['transit_details']
            linha = detalhes['line']
            instrucao = f"🚌 Pegue o {linha['short_name']} - {linha['name']}"
        
        resposta += f"{i}. {instrucao} ({etapa['duration']['text']})\n"
    
    return resposta


def gerar_rota_simulada_elaborada(origem, destino, modo):
    """
    Fallback caso a API do Google falhe
    """
    return "❌ Não foi possível calcular a rota no momento. Tente novamente em alguns instantes."


def handle_request(parameters, escolha_transporte=None):
    """
    Lógica principal para consultar rotas
    """
    origem = parameters.get('origem', '').strip()
    destino = parameters.get('destino', '').strip()
    modo_transporte = parameters.get('modo_transporte', '').lower()
    
    # Se receber uma escolha de transporte, processa
    if escolha_transporte and escolha_transporte.isdigit():
        modo, tag = interpretar_escolha_transporte(int(escolha_transporte))
        if modo:
            modo_transporte = modo
        else:
            return "❌ Opção inválida. " + formatar_lista_transportes()
    
    # Se não tiver modo de transporte, mostra lista
    if not modo_transporte:
        return formatar_lista_transportes()
    
    # Se não tiver origem ou destino, pede
    if not origem or not destino:
        if not origem:
            return "📍 *De onde você está saindo?*"
        else:
            return "🎯 *Para onde você quer ir?*"
    
    # Agora calcula a rota
    try:
        resultado = consultar_google_maps(origem, destino, modo_transporte, GOOGLE_MAPS_API_KEY)
        
        if resultado.get('status') == 'OK' and resultado['routes']:
            return formatar_resposta_google_maps(resultado, origem, destino, modo_transporte)
        else:
            erro = resultado.get('error_message', 'Erro na consulta da rota')
            return f"❌ {erro}"
            
    except Exception as e:
        print(f"Erro ao calcular rota: {e}")
        return "❌ Erro temporário no sistema. Tente em alguns instantes."