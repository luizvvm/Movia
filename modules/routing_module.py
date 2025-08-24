import requests
from config import GOOGLE_MAPS_API_KEY

def handle_request(parameters):
    """
    Lógica para consultar e sugerir rotas integrando com Google Directions API.
    """
    origem = parameters.get('origem', '').strip()
    destino = parameters.get('destino', '').strip()
    modo_transporte = parameters.get('modo_transporte', 'transit').lower()
    
    # Validação básica
    if not origem or not destino:
        return "❌ Preciso saber de onde você está saindo e para onde quer ir. Por favor, informe origem e destino."
    
    # Modo de desenvolvimento - se não tiver chave API
    if not GOOGLE_MAPS_API_KEY or GOOGLE_MAPS_API_KEY == "sua_chave_google_maps_aqui":
        return gerar_rota_simulada(origem, destino, modo_transporte)
    
    try:
        # Consulta a API do Google Maps
        rota = consultar_google_maps(origem, destino, modo_transporte)
        
        if rota:
            return formatar_resposta(rota, origem, destino, modo_transporte)
        else:
            return "❌ Não consegui encontrar rotas para esse trajeto. Verifique se os locais estão corretos."
            
    except Exception as e:
        print(f"Erro ao consultar rotas: {e}")
        return "⚠️ Desculpe, estou com problemas para acessar o sistema de rotas. Tente novamente em alguns instantes."


def consultar_google_maps(origem, destino, modo):
    """
    Consulta a Google Directions API para obter rotas
    """
    # Mapeamento de modos de transporte
    modos_api = {
        'onibus': 'transit',
        'metro': 'transit', 
        'transit': 'transit',
        'bicicleta': 'bicycling',
        'bike': 'bicycling',
        'caminhada': 'walking',
        'walking': 'walking',
        'carro': 'driving',
        'driving': 'driving'
    }
    
    modo_api = modos_api.get(modo, 'transit')
    
    url = "https://maps.googleapis.com/maps/api/directions/json"
    
    params = {
        'origin': origem,
        'destination': destino,
        'mode': modo_api,
        'alternatives': 'true',
        'language': 'pt-BR',
        'region': 'br',
        'key': GOOGLE_MAPS_API_KEY
    }
    
    # Configurações específicas para transporte público
    if modo_api == 'transit':
        params['transit_mode'] = 'bus|subway'
        params['transit_routing_preference'] = 'fewer_transfers'
    
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    
    if data['status'] == 'OK' and data['routes']:
        return data
    else:
        return None


def formatar_resposta(data, origem, destino, modo):
    """
    Formata a resposta da API para uma mensagem amigável no WhatsApp
    """
    rota = data['routes'][0]
    perna = rota['legs'][0]
    
    # Emoji baseado no modo de transporte
    emojis = {
        'transit': '🚍',
        'bicycling': '🚴‍♂️', 
        'walking': '🚶‍♂️',
        'driving': '🚗'
    }
    
    emoji = emojis.get(modo, '📍')
    
    # Nome do modo em português
    nomes_modos = {
        'transit': 'Transporte Público',
        'bicycling': 'Bicicleta',
        'walking': 'Caminhada', 
        'driving': 'Carro'
    }
    
    nome_modo = nomes_modos.get(modo, 'Transporte Público')
    
    # Construindo a resposta
    resposta = f"{emoji} *ROTA DE {nome_modo.upper()}*\n\n"
    resposta += f"📍 *Origem:* {origem.title()}\n"
    resposta += f"🎯 *Destino:* {destino.title()}\n\n"
    
    resposta += "📋 *Instruções da Rota:*\n"
    
    # Adiciona cada etapa da rota
    for i, etapa in enumerate(perna['steps'], 1):
        instrucao = etapa['html_instructions']
        
        # Limpa tags HTML
        instrucao = instrucao.replace('<b>', '').replace('</b>', '')
        instrucao = instrucao.replace('<div style="font-size:0.9em">', ' (')
        instrucao = instrucao.replace('</div>', ')')
        
        # Emoji para a etapa
        modo_etapa = etapa.get('travel_mode', '').lower()
        emoji_etapa = {
            'walking': '🚶‍♂️',
            'transit': '🚌',
            'bicycling': '🚴‍♂️'
        }.get(modo_etapa, '📍')
        
        # Informações de transporte público
        if modo_etapa == 'transit' and 'transit_details' in etapa:
            detalhes = etapa['transit_details']
            linha = detalhes['line']
            tipo_veiculo = linha.get('vehicle', {}).get('type', '').lower()
            
            if tipo_veiculo == 'bus':
                emoji_etapa = '🚌'
                veiculo_texto = 'Ônibus'
            elif tipo_veiculo == 'subway':
                emoji_etapa = '🚇' 
                veiculo_texto = 'Metrô'
            else:
                veiculo_texto = 'Transporte'
            
            numero_linha = linha.get('short_name', '')
            instrucao = f"{emoji_etapa} Pegue o {veiculo_texto} {numero_linha}"
        
        resposta += f"{i}. {emoji_etapa} {instrucao} ({etapa['duration']['text']})\n"
    
    # Informações finais
    resposta += f"\n⏰ *Tempo total:* {perna['duration']['text']}\n"
    resposta += f"📏 *Distância total:* {perna['distance']['text']}\n\n"
    
    # Dica final
    resposta += "💡 *Dica:* Use o Google Maps para navegação em tempo real!"
    
    return resposta


def gerar_rota_simulada(origem, destino, modo):
    """Gera uma rota simulada para desenvolvimento"""
    
    emojis = {
        'onibus': '🚌',
        'metro': '🚇',
        'transit': '🚍',
        'bicicleta': '🚴‍♂️',
        'bike': '🚴‍♂️',
        'caminhada': '🚶‍♂️',
        'walking': '🚶‍♂️',
        'carro': '🚗',
        'driving': '🚗'
    }
    
    emoji = emojis.get(modo, '🚌')
    
    return f"""
{emoji} *ROTA SIMULADA - MODO DESENVOLVIMENTO*

📍 *Origem:* {origem.title()}
🎯 *Destino:* {destino.title()}

📋 *Instruções:*
1. 🚶‍♂️ Caminhe até a parada mais próxima (5 min)
2. {emoji} Pegue o {modo} 123 em direção ao centro (20 min)
3. 🚶‍♂️ Caminhe até o destino final (8 min)

⏰ *Tempo total:* 33 min
📏 *Distância:* 7,5 km

💡 *Dica:* Esta é uma rota simulada. Para rotas reais, configure a API do Google Maps.
"""


# Para teste local (opcional)
if __name__ == "__main__":
    # Teste rápido
    teste_params = {
        'origem': 'copacabana rio de janeiro',
        'destino': 'ipanema rio de janeiro',
        'modo_transporte': 'onibus'
    }
    
    resultado = handle_request(teste_params)
    print(resultado)