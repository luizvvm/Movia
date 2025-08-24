# routing_module.py
import requests
from config import GOOGLE_MAPS_API_KEY

# --- Lista de transportes ---
def gerar_lista_transportes_publicos():
    transportes = [
        {'emoji': '🚌', 'nome': 'Ônibus', 'modo': 'onibus', 'tag': 'bus'},
        {'emoji': '🚇', 'nome': 'Metrô', 'modo': 'metro', 'tag': 'subway'},
        {'emoji': '🚆', 'nome': 'Trem', 'modo': 'trem', 'tag': 'train'},
        {'emoji': '🚋', 'nome': 'VLT', 'modo': 'vlt', 'tag': 'tram'},
        {'emoji': '⛴️', 'nome': 'Barca', 'modo': 'barca', 'tag': 'ferry'},
        {'emoji': '🚴‍♂️', 'nome': 'Bicicleta', 'modo': 'bicicleta', 'tag': 'bicycling'},
        {'emoji': '🚶‍♂️', 'nome': 'Caminhada', 'modo': 'caminhada', 'tag': 'walking'}
    ]
    return transportes

def formatar_lista_transportes():
    transportes = gerar_lista_transportes_publicos()
    mensagem = "🚍 *Como você prefere ir?*\n\n"
    for transp in transportes:
        mensagem += f"{transp['numero']}. {transp['emoji']} {transp['nome']}\n"
    mensagem += "\n*Digite o transporte desejado ou 'ok' para gerar a rota:*"
    return mensagem

# --- Interpretadores ---
def interpretar_escolha_transporte_nome(nome):
    mapping = {
        'ônibus': ('onibus', 'bus'),
        'onibus': ('onibus', 'bus'),
        'metrô': ('metro', 'subway'),
        'metro': ('metro', 'subway'),
        'trem': ('trem', 'train'),
        'vlt': ('vlt', 'tram'),
        'barca': ('barca', 'ferry'),
        'bicicleta': ('bicicleta', 'bicycling'),
        'bike': ('bicicleta', 'bicycling'),
        'caminhada': ('caminhada', 'walking'),
        'a pé': ('caminhada', 'walking')
    }
    return mapping.get(nome.lower(), (None, None))

def get_lista_transportes():
    return list(interpretar_escolha_transporte_nome.mapping.keys()) if hasattr(interpretar_escolha_transporte_nome, "mapping") else [
        'ônibus','onibus','metrô','metro','trem','vlt','barca','bicicleta','bike','caminhada','a pé'
    ]

# --- Google Maps ---
def consultar_google_maps(origem, destino, modo_transporte="transit", api_key=None):
    url = "https://maps.googleapis.com/maps/api/directions/json"
    modos_api = {
        'onibus': 'transit',
        'metro': 'transit', 
        'metrô': 'transit',
        'trem': 'transit',
        'vlt': 'transit',
        'barca': 'transit',
        'bicicleta': 'bicycling',
        'bike': 'bicycling',
        'caminhada': 'walking',
        'walking': 'walking'
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
    if modo_api == 'transit':
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
            params["transit_mode"] = "bus|subway|train|tram|ferry"
        params["transit_routing_preference"] = "fewer_transfers"
    response = requests.get(url, params=params, timeout=10)
    return response.json()

def formatar_resposta_google_maps(data, origem, destino, modo):
    try:
        rota = data['routes'][0]
        perna = rota['legs'][0]
        tempo_total = perna['duration']['text']
        distancia_total = perna['distance']['text']
        resposta = f"🚍 *ROTA DE {modo.upper()}*\n\n"
        resposta += f"📍 *De:* {origem.title()}\n"
        resposta += f"🎯 *Para:* {destino.title()}\n"
        resposta += f"⏰ *Tempo:* {tempo_total}\n"
        resposta += f"📏 *Distância:* {distancia_total}\n\n"
        resposta += "📋 *Instruções:*\n"
        for i, etapa in enumerate(perna['steps'][:5], 1):
            instrucao = etapa['html_instructions'].replace('<b>', '').replace('</b>', '')
            instrucao = instrucao.replace('<div style="font-size:0.9em">', ' (').replace('</div>', ')')
            emoji = '📍'
            if 'transit' in etapa.get('travel_mode', '').lower():
                emoji = '🚌'
            elif 'walking' in etapa.get('travel_mode', '').lower():
                emoji = '🚶‍♂️'
            resposta += f"{i}. {emoji} {instrucao} ({etapa['duration']['text']})\n"
        return resposta
    except:
        return f"❌ Não foi possível formatar a rota."

# --- Rota simulada ---
def gerar_rota_simulada(origem, destino, modo):
    return f"🚌 *Rota simulada de {origem} para {destino}:*\n- Pegue a Linha 472 (Triagem - Leme).\n- Tempo estimado: 35 minutos.\n- Valor da passagem: R$ 4,30."

# --- Handle request ---
def handle_request(parameters, frase_usuario=None, escolha_transporte=None):
    origem = parameters.get('origem', '').strip()
    destino = parameters.get('destino', '').strip()
    modo_transporte = parameters.get('modo_transporte', '').lower() if parameters.get('modo_transporte') else ''

    # Detecta modo pela frase
    if frase_usuario and not modo_transporte:
        frase = frase_usuario.lower()
        for nome in get_lista_transportes():
            if nome in frase:
                modo_transporte = interpretar_escolha_transporte_nome(nome)[0]
                break

    # Se receber escolha escrita
    if escolha_transporte:
        modo, tag = interpretar_escolha_transporte_nome(escolha_transporte)
        if modo:
            modo_transporte = modo
        else:
            return "❌ Transporte inválido. " + formatar_lista_transportes()

    # Sem modo, retorna lista
    if not modo_transporte:
        return formatar_lista_transportes()

    # Sem origem ou destino
    if not origem:
        return "📍 *De onde você está saindo?*"
    if not destino:
        return "🎯 *Para onde você quer ir?*"

    # Consulta API ou gera rota simulada
    if not GOOGLE_MAPS_API_KEY or GOOGLE_MAPS_API_KEY == "sua_chave_google_maps_aqui":
        return gerar_rota_simulada(origem, destino, modo_transporte)

    try:
        resultado = consultar_google_maps(origem, destino, modo_transporte, GOOGLE_MAPS_API_KEY)
        if resultado.get('status') == 'OK' and resultado['routes']:
            return formatar_resposta_google_maps(resultado, origem, destino, modo_transporte)
        else:
            return gerar_rota_simulada(origem, destino, modo_transporte)
    except Exception as e:
        print(f"Erro: {e}")
        return gerar_rota_simulada(origem, destino, modo_transporte)
