# routing_module.py
import requests
from config import GOOGLE_MAPS_API_KEY
import re, random

def distribuir_transportes(escolhidos):
    """
    Recebe uma lista de transportes escolhidos pelo usuário.
    Retorna uma lista de 5 transportes para cada rota, distribuídos conforme:
    - 1 transporte: todas as 5 rotas iguais
    - 2 transportes: primeira rota do 1º, segunda do 2º, as 3 restantes misturam
    - 3 transportes: primeiras 3 rotas com cada transporte, últimas 2 misturam
    """
    total_rotas = 5
    modos = []

    n = len(escolhidos)

    if n == 0:
        return []  # sem transporte definido
    elif n == 1:
        modos = [escolhidos[0]] * total_rotas
    elif n == 2:
        modos = [escolhidos[0], escolhidos[1]]
        modos += [random.choice(escolhidos) for _ in range(total_rotas - 2)]
    elif n >= 3:
        modos = escolhidos[:3]
        modos += [random.choice(escolhidos) for _ in range(total_rotas - 3)]

    # opcional: embaralhar para não ficar sempre na mesma ordem
    random.shuffle(modos)
    return modos


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
        "region": "br",
        "alternatives": "true"  # 👈 habilita rotas alternativas
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
    vehicle = (line.get('vehicle') or {}).get('type', '').upper()
    line_name = (line.get('name') or '').strip()
    short = (line.get('short_name') or '').strip()

    texto_linha = f"{line_name} {short}".lower()
    
    # Detecta BRT pelo nome
    if 'brt' in texto_linha or 'transbrasil' in texto_linha or 'transcarioca' in texto_linha:
        tipo_real = 'BRT'
    elif 'metro' in texto_linha or 'linha' in texto_linha:
        tipo_real = 'Metrô'
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
    return rotulo, tipo_real

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

def handle_request(parameters, frase_usuario=None, escolha_transporte=None):
    origem = parameters.get('origem', '').strip()
    destino = parameters.get('destino', '').strip()
    
    escolhidos = []
    
    if isinstance(escolha_transporte, list):
        escolhidos = escolha_transporte
    elif escolha_transporte:
        modo, _ = interpretar_escolha_transporte_nome(escolha_transporte)
        if modo:
            escolhidos.append(modo)
        else:
            return "❌ Transporte inválido.\n" + formatar_lista_transportes()
    
    if frase_usuario:
        frase = frase_usuario.lower()
        for nome in get_lista_transportes():
            if nome in frase:
                modo, _ = interpretar_escolha_transporte_nome(nome)
                if modo:
                    escolhidos.append(modo)

    if not escolhidos:
        return formatar_lista_transportes()

    if not origem:
        return "📍 *De onde você está saindo?*"
    if not destino:
        return "🎯 *Para onde você quer ir?*"

    todas_rotas = []
    modos_ja_consultados = set()

    for modo in escolhidos:
        if modo in modos_ja_consultados:
            continue
        modos_ja_consultados.add(modo)
        
        try:
            resultado = consultar_google_maps(origem, destino, modo_transporte=modo, api_key=GOOGLE_MAPS_API_KEY)
            if resultado.get('status') == 'OK' and resultado.get('routes'):
                for rota in resultado['routes'][:2]:
                    rota['modo_consulta'] = modo
                    todas_rotas.append(rota)
        except Exception as e:
            print(f"Erro ao consultar modo {modo}: {e}")
            continue

    if len(todas_rotas) < 5:
        try:
            resultado = consultar_google_maps(origem, destino, modo_transporte="transit", api_key=GOOGLE_MAPS_API_KEY)
            if resultado.get('status') == 'OK' and resultado.get('routes'):
                for rota in resultado['routes'][:5 - len(todas_rotas)]:
                    if not any(r['overview_polyline'] == rota['overview_polyline'] for r in todas_rotas):
                        rota['modo_consulta'] = 'transit'
                        todas_rotas.append(rota)
        except Exception as e:
            print(f"Erro ao consultar modo geral: {e}")

    rotas_unicas = []
    rotas_vistas = set()

    for rota in todas_rotas:
        rota_id = rota.get('overview_polyline', {}).get('points', '') if isinstance(rota.get('overview_polyline'), dict) else rota.get('overview_polyline', '')
        
        if rota_id and rota_id not in rotas_vistas:
            rotas_vistas.add(rota_id)
            rotas_unicas.append(rota)

    rotas_selecionadas = rotas_unicas[:5]
    
    if rotas_selecionadas:
        resposta_formatada = formatar_resposta_google_maps(rotas_selecionadas, origem, destino)
        
        if resposta_formatada is None:
            resposta_formatada = "❌ Ocorreu um erro ao formatar as rotas."
        else:
            try:
                from services import database_service
                database_service.salvar_rotas_usuario("user_id_temporario", rotas_selecionadas)
            except Exception as e:
                print(f"⚠️ Erro ao salvar rotas: {e}")
            
            resposta_formatada += "\n\n🌟 *Como você prefere sua rota?*\n"
            resposta_formatada += "• 🚀 *Mais rápida* - Menor tempo de viagem\n"
            resposta_formatada += "• 🛡️ *Mais segura* - Rotas com melhor iluminação e movimento\n"
            resposta_formatada += "• 💰 *Mais econômica* - Menor custo com transporte\n"
            resposta_formatada += "• 🌿 *Mais sustentável* - Menor impacto ambiental\n"
            resposta_formatada += "• 🤝 *Mais acessível* - Melhor para pessoas com mobilidade reduzida\n\n"
            resposta_formatada += "Digite sua preferência!"
        
        return resposta_formatada
    else:
        return "❌ Não encontrei rotas para esse trajeto."
def formatar_resposta_google_maps(rotas, origem, destino):
    if not rotas:
        return "❌ Não encontrei rotas para esse trajeto."

    resposta = f"📍 *Rotas de {origem.title()} até {destino.title()}:*\n\n"
    
    for idx, rota in enumerate(rotas):
        leg = rota['legs'][0]
        duracao_total = leg['duration']['text']
        distancia_total = leg['distance']['text']
        
        # Conta os tipos de transporte
        contagem_transportes = {}
        
        for step in leg['steps']:
            if step.get('travel_mode') == 'TRANSIT':
                transit_details = step.get('transit_details', {})
                _, tipo_real = _rotulo_transporte(transit_details)
                contagem_transportes[tipo_real] = contagem_transportes.get(tipo_real, 0) + 1
        
        # Cria label descritiva
        if contagem_transportes:
            partes = []
            for transporte, quantidade in contagem_transportes.items():
                if quantidade > 1:
                    partes.append(f"{quantidade}x {transporte}")
                else:
                    partes.append(transporte)
            label_transporte = " + ".join(partes)
        else:
            label_transporte = "Apenas caminhada"
        
        resposta += f"➡️ *Opção {idx+1} ({label_transporte})*: {distancia_total}, {duracao_total}\n"
        
        # Instruções detalhadas
        for i, step in enumerate(leg['steps']):
            if step.get('travel_mode') == 'WALKING':
                instrucao = _limpar_html(step.get('html_instructions', ''))
                # Encurta instruções muito longas
                if len(instrucao) > 40:
                    instrucao = instrucao[:40] + "..."
                resposta += f"   - 🚶 {instrucao} ({step['duration']['text']})\n"
                
            elif step.get('travel_mode') == 'TRANSIT':
                transit_details = step.get('transit_details', {})
                rotulo, tipo_real = _rotulo_transporte(transit_details)
                
                # Informações específicas do transporte
                num_veiculo = transit_details.get('line', {}).get('short_name', '')
                destino_veiculo = transit_details.get('headsign', '')
                ponto_embarque = transit_details.get('departure_stop', {}).get('name', '')
                ponto_desembarque = transit_details.get('arrival_stop', {}).get('name', '')
                
                # Formata a instrução com ponto de desembarque
                if tipo_real in ['Ônibus', 'BRT']:
                    if num_veiculo:
                        resposta += f"   - 🚌 Pegue o {tipo_real} {num_veiculo} para {destino_veiculo} em {ponto_embarque} - Vá até {ponto_desembarque} ({step['duration']['text']})\n"
                    else:
                        resposta += f"   - 🚌 Pegue o {tipo_real} para {destino_veiculo} em {ponto_embarque} - Vá até {ponto_desembarque} ({step['duration']['text']})\n"
                
                elif tipo_real == 'Metrô':
                    if num_veiculo:
                        resposta += f"   - 🚇 Pegue a Linha {num_veiculo} do Metrô para {destino_veiculo} em {ponto_embarque} - Desça em {ponto_desembarque} ({step['duration']['text']})\n"
                    else:
                        resposta += f"   - 🚇 Pegue o Metrô para {destino_veiculo} em {ponto_embarque} - Desça em {ponto_desembarque} ({step['duration']['text']})\n"
                
                elif tipo_real == 'Trem':
                    if num_veiculo:
                        resposta += f"   - 🚆 Pegue o Trem {num_veiculo} para {destino_veiculo} em {ponto_embarque} - Desça em {ponto_desembarque} ({step['duration']['text']})\n"
                    else:
                        resposta += f"   - 🚆 Pegue o Trem para {destino_veiculo} em {ponto_embarque} - Desça em {ponto_desembarque} ({step['duration']['text']})\n"
                
                elif tipo_real == 'VLT':
                    resposta += f"   - 🚋 Pegue o VLT para {destino_veiculo} em {ponto_embarque} - Desça em {ponto_desembarque} ({step['duration']['text']})\n"
                
                elif tipo_real == 'Barca':
                    resposta += f"   - ⛴️ Pegue a Barca para {destino_veiculo} em {ponto_embarque} - Desembarque em {ponto_desembarque} ({step['duration']['text']})\n"
        
        resposta += "\n"
    
    return resposta  # 👈 CERTIFIQUE-SE QUE ESTÁ RETORNANDO A RESPOSTA!
    
def handle_request(parameters, frase_usuario=None, escolha_transporte=None):
    origem = parameters.get('origem', '') or ''
    destino = parameters.get('destino', '') or ''
    origem = origem.strip() if origem else ''
    destino = destino.strip() if destino else ''
    
    escolhidos = []
    
    if isinstance(escolha_transporte, list):
        escolhidos = escolha_transporte
    elif escolha_transporte:
        if isinstance(escolha_transporte, str):
            modo, _ = interpretar_escolha_transporte_nome(escolha_transporte)
            if modo:
                escolhidos.append(modo)
            else:
                return "❌ Transporte inválido.\n" + formatar_lista_transportes()
    
    if frase_usuario:
        frase = frase_usuario.lower()
        for nome in get_lista_transportes():
            if nome in frase:
                modo, _ = interpretar_escolha_transporte_nome(nome)
                if modo:
                    escolhidos.append(modo)

    if not escolhidos:
        return formatar_lista_transportes()

    if not origem:
        return "📍 *De onde você está saindo?*"
    if not destino:
        return "🎯 *Para onde você quer ir?*"

    todas_rotas = []
    modos_ja_consultados = set()

    for modo in escolhidos:
        if modo in modos_ja_consultados:
            continue
        modos_ja_consultados.add(modo)
        
        try:
            resultado = consultar_google_maps(origem, destino, modo_transporte=modo, api_key=GOOGLE_MAPS_API_KEY)
            if resultado.get('status') == 'OK' and resultado.get('routes'):
                for rota in resultado['routes'][:2]:
                    rota['modo_consulta'] = modo
                    todas_rotas.append(rota)
        except Exception as e:
            print(f"Erro ao consultar modo {modo}: {e}")
            continue

    if len(todas_rotas) < 5:
        try:
            resultado = consultar_google_maps(origem, destino, modo_transporte="transit", api_key=GOOGLE_MAPS_API_KEY)
            if resultado.get('status') == 'OK' and resultado.get('routes'):
                for rota in resultado['routes'][:5 - len(todas_rotas)]:
                    if not any(r['overview_polyline'] == rota['overview_polyline'] for r in todas_rotas):
                        rota['modo_consulta'] = 'transit'
                        todas_rotas.append(rota)
        except Exception as e:
            print(f"Erro ao consultar modo geral: {e}")

    rotas_unicas = []
    rotas_vistas = set()

    for rota in todas_rotas:
        rota_id = rota.get('overview_polyline', {}).get('points', '') if isinstance(rota.get('overview_polyline'), dict) else rota.get('overview_polyline', '')
        
        if rota_id and rota_id not in rotas_vistas:
            rotas_vistas.add(rota_id)
            rotas_unicas.append(rota)

    rotas_selecionadas = rotas_unicas[:5]
    
    if rotas_selecionadas:
        resposta_formatada = formatar_resposta_google_maps(rotas_selecionadas, origem, destino)
        
        if resposta_formatada is None:
            resposta_formatada = "❌ Ocorreu um erro ao formatar as rotas."
        else:
            try:
                from services import database_service
                database_service.salvar_rotas_usuario("user_id_temporario", rotas_selecionadas)
            except Exception as e:
                print(f"⚠️ Erro ao salvar rotas: {e}")
            
            resposta_formatada += "\n\n🌟 *Como você prefere sua rota?*\n"
            resposta_formatada += "• 🚀 *Mais rápida* - Menor tempo de viagem\n"
            resposta_formatada += "• 🛡️ *Mais segura* - Rotas com melhor iluminação e movimento\n"
            resposta_formatada += "• 💰 *Mais econômica* - Menor custo com transporte\n"
            resposta_formatada += "• 🌿 *Mais sustentável* - Menor impacto ambiental\n"
            resposta_formatada += "• 🤝 *Mais acessível* - Melhor para pessoas com mobilidade reduzida\n\n"
            resposta_formatada += "Digite sua preferência!"
        
        return resposta_formatada
    else:
        return "❌ Não encontrei rotas para esse trajeto."