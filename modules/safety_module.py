# modules/safety_module.py
# VERSÃO DE PROTÓTIPO COM DADOS ESTÁTICOS (MOCK)

# -------------------------
# Dados Estáticos (Mock Data)
# -------------------------
# Esta lista de dicionários simula os dados que seriam obtidos de uma API.
# Os dados fornecidos foram pré-processados e filtrados para o município do "Rio de Janeiro".
_MOCK_DATA = [
    {'data': '26/08/25 17:51', 'ocorrencia': 'Disparos ouvidos', 'bairro': 'Penha Circular'},
    {'data': '26/08/25 13:47', 'ocorrencia': 'Disparos ouvidos', 'bairro': 'Vila da Penha'},
    {'data': '26/08/25 12:12', 'ocorrencia': 'Disparos ouvidos', 'bairro': 'Madureira'},
    {'data': '26/08/25 10:43', 'ocorrencia': 'Disparos ouvidos', 'bairro': 'Piedade'},
    {'data': '26/08/25 09:03', 'ocorrencia': 'Disparos ouvidos', 'bairro': 'Penha Circular'},
    {'data': '26/08/25 07:03', 'ocorrencia': 'Operação Policial', 'bairro': 'Quintino Bocaiúva'},
    {'data': '26/08/25 06:32', 'ocorrencia': 'Tiroteio', 'bairro': 'Penha'},
    {'data': '26/08/25 06:30', 'ocorrencia': 'Tiroteio', 'bairro': 'Inhaúma'},
    {'data': '26/08/25 06:27', 'ocorrencia': 'Tiroteio', 'bairro': 'Cavalcanti'},
    {'data': '26/08/25 06:24', 'ocorrencia': 'Tiroteio', 'bairro': 'Vila da Penha'},
    {'data': '26/08/25 06:23', 'ocorrencia': 'Tiroteio', 'bairro': 'Penha'},
    {'data': '26/08/25 06:05', 'ocorrencia': 'Operação Policial', 'bairro': 'Madureira'},
    {'data': '26/08/25 05:59', 'ocorrencia': 'Disparos ouvidos', 'bairro': 'Vila da Penha'},
    {'data': '26/08/25 05:56', 'ocorrencia': 'Tiroteio', 'bairro': 'Madureira'},
    {'data': '26/08/25 05:55', 'ocorrencia': 'Disparos ouvidos', 'bairro': 'Engenho da Rainha'},
    {'data': '26/08/25 05:55', 'ocorrencia': 'Tiroteio', 'bairro': 'Inhaúma'},
    {'data': '26/08/25 02:36', 'ocorrencia': 'Disparos ouvidos', 'bairro': 'Andaraí'},
]

# -------------------------
# Função de "Busca"
# -------------------------
def _get_mock_incidents():
    """
    Esta função simula uma chamada de API, mas simplesmente retorna
    a nossa lista de dados estáticos.
    """
    return _MOCK_DATA

# -------------------------
# Função Principal (Interface Pública do Módulo)
# -------------------------
def handle_request(parameters):
    """
    Processa a requisição do usuário, busca nos dados estáticos e formata a resposta.
    """
    # Extrai o bairro (local) dos parâmetros enviados pela IA
    local = parameters.get("local") or parameters.get("bairro") or parameters.get("linha") # Aceita variações
    
    all_incidents = _get_mock_incidents()
    
    # Se o usuário não especificou um local, usaremos todos os incidentes
    incidents_to_show = all_incidents
    
    # Se um local foi especificado, filtra a lista
    if local:
        local = local.lower()
        # Filtra a lista para incluir apenas incidentes cujo bairro contenha o texto pesquisado
        incidents_to_show = [
            inc for inc in all_incidents 
            if local in inc.get('bairro', '').lower()
        ]

    # Se a lista (filtrada ou não) estiver vazia, retorna uma mensagem padrão
    if not incidents_to_show:
        if local:
            return f"Não encontrei registros de segurança para '{local.title()}' nos dados de hoje."
        else:
            return "Não encontrei nenhum registro de segurança nos dados de hoje."

    # Monta a resposta para o usuário
    if local:
        resposta = f"Com base nos dados disponíveis, encontrei {len(incidents_to_show)} registro(s) para '{local.title()}':\n"
    else:
        resposta = f"Com base nos dados disponíveis, aqui estão os registros mais recentes:\n"

    # Adiciona até 5 incidentes na resposta para não sobrecarregar o usuário
    for inc in incidents_to_show[:5]:
        ocorrencia = inc.get('ocorrencia', 'Evento')
        bairro = inc.get('bairro', 'N/A')
        # Extrai apenas o horário da string de data
        horario = inc.get('data', 'N/A').split(' ')[-1]

        resposta += f"\n- *{ocorrencia}* em {bairro} (às {horario})"
        
    return resposta.strip()
