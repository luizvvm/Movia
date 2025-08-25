# routing_module.py
import requests
from config import GOOGLE_MAPS_API_KEY
import re, random

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
    for i, transp in enumerate(transportes, 1):
        mensagem += f"{transp['emoji']} {transp['nome']}\n"
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
        params["departure_time"] = "now"  # 👈 adicionar isto

    response = requests.get(url, params=params, timeout=10)
    return response.json()

def _limpar_html(txt: str) -> str:
    if not txt:
        return ""
    # transforma aquele <div style="font-size:0.9em"> em parênteses
    txt = txt.replace('<div style="font-size:0.9em">', ' (').replace('</div>', ')')
    # remove <b> e </b>
    txt = txt.replace('<b>', '').replace('</b>', '')
    # remove o restante de tags
    txt = re.sub(r'<.*?>', '', txt)
    return txt

def _rotulo_transporte(transit_details: dict) -> tuple:
    """
    Retorna o rótulo do transporte e o tipo real: BRT, Trem, VLT, Metrô, Ônibus, Barca, etc.
    """
    line = (transit_details or {}).get('line', {}) or {}
    vehicle = (line.get('vehicle') or {}).get('type', '').upper()  # BUS, TRAM, SUBWAY, HEAVY_RAIL, FERRY...
    line_name = (line.get('name') or '').strip()
    short = (line.get('short_name') or '').strip()

    texto_linha = f"{line_name} {short}".lower()
    
    # Detecta BRT pelo nome
    if 'brt' in texto_linha:
        tipo_real = 'BRT'
    else:
        mapa = {
            'BUS': 'Ônibus',
            'TRAM': 'VLT',
            'SUBWAY': 'Metrô',
            'HEAVY_RAIL': 'Trem',
            'RAIL': 'Trem',
            'FERRY': 'Barca'
        }
        tipo_real = mapa.get(vehicle, vehicle or 'Transporte')

    numero_ou_nome = short or line_name or ''
    rotulo = f"{tipo_real} {numero_ou_nome}".strip()
    return rotulo, tipo_real  # retorna rótulo + tipo real

def obter_pontos_de_referencia(lat, lng, raio=100):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": raio,
        "key": GOOGLE_MAPS_API_KEY,
        "language": "pt-BR"
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    pontos_referencia = []
    for lugar in data.get('results', [])[:5]:  # Limita a 5 resultados
        pontos_referencia.append({
            'nome': lugar.get('name'),
            'tipo': lugar.get('types', [])[0] if lugar.get('types') else '',
            'proximidade': 'próximo'  # Você pode calcular a distância exata
        })
    
    return pontos_referencia

def obter_ponto_referencia_simulado(instrucao):
    """Retorna pontos de referência que fazem sentido com a instrução"""
    
    # Se a instrução já tem um destino específico, usa referências diferentes
    if "para " in instrucao.lower():
        pontos = [
            "passando por uma padaria", 
            "virando próximo a um supermercado",
            "cruzando perto de uma farmácia",
            "avançando após um posto de gasolina",
            "seguindo junto a uma praça",
            "contornando um restaurante",
            "contornando uma escola"
        ]
    else:
        pontos = [
            "passe por uma padaria",
            "vá além do supermercado", 
            "siga após a farmácia",
            "avance passando o posto",
            "corte a praça",
            "contorne o restaurante"
        ]
    
    import random
    return random.choice(pontos)

def calcular_preco_transporte(modo_transporte):
    """Retorna preço aproximado do transporte público no RJ"""
    tabela_preco = {
        'onibus': 4.70,      
        'metro': 7.90,       
        'metrô': 7.90,
        'trem': 7.60,
        'vlt': 4.70,
        'barca': 4.70        
    }
    return tabela_preco.get(modo_transporte, 4.70)  # default 4,70


def formatar_instrucao_com_referencia(instrucao, modo):
    """Adiciona ponto de referência à instrução"""
    if modo == 'walking':
        referencia = obter_ponto_referencia_simulado("caminhada")
        return f"passe por {referencia} e {instrucao.lower()}"
    return instrucao

def formatar_resposta_google_maps(data, origem, destino, modo):
    """
    Formata a resposta da rota obtida do Google Maps:
    - Caminhada curta até parada/estação de transporte: instrução única
    - Caminhadas longas: ponto de referência
    - Transporte: linha, parada/estação de partida, chegada, duração e emoji
    """
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

        contador = 1
        preco_total = 0.0
        ultimo_transporte = None  # guarda o transporte do trecho anterior

        steps = perna['steps']
        i = 0
        while i < len(steps):
            etapa = steps[i]
            travel_mode = etapa.get('travel_mode', '').lower()
            instrucao = _limpar_html(etapa.get('html_instructions', ''))
            distancia_etapa = etapa.get('distance', {}).get('value', 0)  # em metros

            # --- Caminhadas ---
            if travel_mode == 'walking':
                # Próxima etapa é transporte público
                if i + 1 < len(steps) and steps[i + 1].get('travel_mode', '').lower() == 'transit':
                    prox_etapa = steps[i + 1]
                    transit_details = prox_etapa.get('transit_details', {})
                    rotulo, tipo_real = _rotulo_transporte(transit_details)
                    
                    # Determina tipo do transporte
                    tipo_transporte = tipo_real  # ex: Ônibus, Metrô, BRT
                    nome_local = "estação" if tipo_transporte in ['BRT','Trem','VLT','Metrô','Metro'] else "parada"
                    
                    # Somar preço apenas se transporte mudou
                    modo_trecho = tipo_transporte.lower()
                    if modo_trecho == 'brt':
                        modo_trecho = 'onibus'
                    if modo_trecho != ultimo_transporte:
                        preco_total += calcular_preco_transporte(modo_trecho)
                        ultimo_transporte = modo_trecho

                    departure_stop = transit_details.get('departure_stop', {}).get('name', 'parada')
                    resposta += f"{contador}. 🚶‍♂️ Ande até a {nome_local} de {rotulo} na rua {departure_stop} (aprox. 100m)\n"
                    contador += 1

                    # Transporte
                    arrival_stop = transit_details.get('arrival_stop', {}).get('name', 'destino')
                    duracao = prox_etapa.get('duration', {}).get('text', '')
                    emoji = {
                        'Ônibus': '🚌',
                        'VLT': '🚋',
                        'Metrô': '🚇',
                        'Trem': '🚆',
                        'Barca': '⛴️'
                    }.get(tipo_transporte, '🚌')
                    resposta += f"{contador}. {emoji} Pegue o {rotulo} → desça em {arrival_stop} ({duracao})\n"
                    contador += 1
                    i += 2
                    continue
                else:
                    # Caminhada sem transporte próximo
                    if distancia_etapa >= 200:
                        lat = etapa['start_location']['lat']
                        lng = etapa['start_location']['lng']
                        pontos = obter_pontos_de_referencia(lat, lng)
                        if pontos:
                            referencia = pontos[0]['nome']
                            resposta += f"{contador}. 🚶‍♂️ {instrucao} (passando por {referencia})\n"
                        else:
                            resposta += f"{contador}. 🚶‍♂️ {instrucao}\n"
                    else:
                        resposta += f"{contador}. 🚶‍♂️ {instrucao}\n"
                    contador += 1

            # --- Transporte isolado ---
            elif travel_mode == 'transit':
                transit_details = etapa.get('transit_details', {})
                rotulo, tipo_real = _rotulo_transporte(transit_details)
                
                tipo_transporte = tipo_real
                nome_local = "estação" if tipo_transporte in ['BRT','Trem','VLT','Metrô','Metro'] else "parada"
                
                departure_stop = transit_details.get('departure_stop', {}).get('name', 'ponto inicial')
                arrival_stop = transit_details.get('arrival_stop', {}).get('name', 'ponto final')
                duracao = etapa.get('duration', {}).get('text', '')
                distancia_caminhada = etapa.get('distance', {}).get('value', 100)

                emoji = {
                    'Ônibus': '🚌',
                    'VLT': '🚋',
                    'Metrô': '🚇',
                    'Trem': '🚆',
                    'Barca': '⛴️'
                }.get(tipo_transporte, '🚌')

                resposta += f"{contador}. 🚶‍♂️ Ande {distancia_caminhada}m até a {nome_local} em {departure_stop}\n"
                contador += 1
                resposta += f"{contador}. {emoji} Pegue o {rotulo} → desça em {arrival_stop} ({duracao})\n"

                # Soma o preço do trecho atual
                modo_atual = tipo_transporte.lower()
                if modo_atual == 'brt':
                    modo_atual = 'onibus'
                if modo_atual != ultimo_transporte:
                    preco_total += calcular_preco_transporte(modo_atual)
                    ultimo_transporte = modo_atual

            # --- Outros modos ---
            else:
                resposta += f"{contador}. 📍 {instrucao}\n"
                contador += 1

            i += 1

        resposta += f"\n💰 Valor aproximado total da passagem: R$ {preco_total:.2f}\n"
        return resposta

    except Exception as e:
        print(f"Erro ao formatar rota: {e}")
        return "❌ Não foi possível formatar a rota detalhada."


# --- Rota simulada ---
def gerar_rota_simulada(origem, destino, modo):
    return f"🚌 *Rota simulada de {origem} para {destino}:*\n- Pegue a Linha 472 (Triagem - Leme).\n- Tempo estimado: 35 minutos."

def handle_request(parameters, frase_usuario=None, escolha_transporte=None):
    """
    Processa a requisição do usuário para obter uma rota.
    - Detecta transporte pela frase ou escolha do usuário.
    - Retorna lista de transportes se modo não especificado.
    - Retorna perguntas se origem ou destino estiverem ausentes.
    - Consulta Google Maps ou gera rota simulada se não houver chave.
    """
    origem = parameters.get('origem', '').strip()
    destino = parameters.get('destino', '').strip()
    modo_transporte = parameters.get('modo_transporte', '').lower() if parameters.get('modo_transporte') else ''

    # 1️⃣ Detecta modo de transporte pela frase do usuário
    if frase_usuario and not modo_transporte:
        frase = frase_usuario.lower()
        for nome in get_lista_transportes():
            if nome in frase:
                modo_transporte, _ = interpretar_escolha_transporte_nome(nome)
                break

    # 2️⃣ Detecta modo de transporte pela escolha do usuário
    if escolha_transporte:
        modo, _ = interpretar_escolha_transporte_nome(escolha_transporte)
        if modo:
            modo_transporte = modo
        else:
            return "❌ Transporte inválido.\n" + formatar_lista_transportes()

    # 3️⃣ Se modo não definido, retorna lista de transportes
    if not modo_transporte:
        return formatar_lista_transportes()

    # 4️⃣ Pergunta origem e destino se estiverem faltando
    if not origem:
        return "📍 *De onde você está saindo?*"
    if not destino:
        return "🎯 *Para onde você quer ir?*"

    # 5️⃣ Consulta Google Maps ou gera rota simulada
    if not GOOGLE_MAPS_API_KEY or GOOGLE_MAPS_API_KEY == "sua_chave_google_maps_aqui":
        return gerar_rota_simulada(origem, destino, modo_transporte)

    try:
        resultado = consultar_google_maps(origem, destino, modo_transporte, GOOGLE_MAPS_API_KEY)
        if resultado.get('status') == 'OK' and resultado['routes']:
            return formatar_resposta_google_maps(resultado, origem, destino, modo_transporte)
        else:
            return gerar_rota_simulada(origem, destino, modo_transporte)
    except Exception as e:
        print(f"Erro ao consultar Google Maps: {e}")
        return gerar_rota_simulada(origem, destino, modo_transporte)
    