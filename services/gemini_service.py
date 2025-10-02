# services/gemini_service.py
import json
import re
import google.generativeai as genai
import config

try:
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")
    print("INFO: Modelo Gemini inicializado com sucesso!")
except Exception as e:
    print(f"ERRO CRÍTICO: Falha ao inicializar o modelo Gemini. Verifique a GEMINI_API_KEY. Erro: {e}")
    model = None

def get_intent(contexto_completo):
    """
    Analisa a mensagem do usuário no contexto do histórico,
    retorna intenção, parâmetros e novo resumo.
    """
    if model is None:
        return analisar_intent_localmente(contexto_completo)
    
    prompt = f"""
    Você é a Mob.IA, assistente de mobilidade do Rio.

    Contexto até agora:
    {contexto_completo}

    Tarefas:
    1. Identifique a intenção principal do usuário.
       Possíveis intents: ["consultar_rota", "consultar_seguranca", "consultar_sustentabilidade", "conversa_geral"].
    2. Extraia parâmetros relevantes (origem, destino, bairro, horário, modal etc).
    3. Gere um resumo atualizado do histórico do usuário em no máximo 3 frases, 
       mantendo preferências e assuntos recorrentes.

    Responda em JSON no formato:
    {{
      "intent": "...",
      "parameters": {{...}},
      "novo_resumo": "..."
    }}
    """
    try:
        resposta = model.generate_content(prompt)  
        cleaned_response = resposta.text.strip().replace('```json', '').replace('```', '').strip()
        dados = json.loads(cleaned_response)
        return dados
    except json.JSONDecodeError as e:
        print(f"❌ JSON inválido do Gemini: {resposta.text if resposta else 'Resposta vazia'}")
        return analisar_intent_localmente(contexto_completo)
    except Exception as e:
        print(f"ERRO em get_intent: {e}")
        return analisar_intent_localmente(contexto_completo)

def analisar_intent_localmente(contexto_completo):
    """
    Fallback para análise local quando o Gemini falha
    """
    mensagem = contexto_completo.lower()
    
    palavras_rota = ['rota', 'como chegar', 'como ir', 'melhor caminho', 'trajeto', 'direções', 'chegar', 'ir para', 'ir até']
    palavras_seguranca = ['seguro', 'segurança', 'perigoso', 'assalto', 'roubo', 'cuidado', 'perigo']
    palavras_sustentabilidade = ['sustentável', 'ecológico', 'meio ambiente', 'poluição', 'carbono', 'verde']
    
    parameters = {}
    intent = 'conversa_geral'
    
    if any(palavra in mensagem for palavra in palavras_rota):
        intent = 'consultar_rota'
        origem, destino = extrair_origem_destino(mensagem)
        if origem and destino:
            parameters = {'origem': origem, 'destino': destino}
    elif any(palavra in mensagem for palavra in palavras_seguranca):
        intent = 'consultar_seguranca'
    elif any(palavra in mensagem for palavra in palavras_sustentabilidade):
        intent = 'consultar_sustentabilidade'
    
    return {
        'intent': intent,
        'parameters': parameters,
        'novo_resumo': contexto_completo[:300]
    }

def extrair_origem_destino(mensagem):
    """
    Tenta extrair origem e destino da mensagem usando regex
    """
    padroes = [
        r'(?:de|do|da|dos|das) (.+?) (?:para|até|ao|a|pro|em|no|na) (.+?)(?:\.|$|\?|!)',
        r'(?:from) (.+?) (?:to) (.+?)(?:\.|$|\?|!)',
        r'como (?:chegar|ir) (?:de|do|da) (.+?) (?:para|até|ao|a) (.+?)(?:\.|$|\?|!)',
        r'rota (?:de|do|da) (.+?) (?:para|até|ao|a) (.+?)(?:\.|$|\?|!)',
        r'qual (?:o|a) (?:caminho|trajeto) (?:de|do|da) (.+?) (?:para|até|ao|a) (.+?)(?:\.|$|\?|!)'
    ]
    
    for padrao in padroes:
        match = re.search(padrao, mensagem, re.IGNORECASE)
        if match:
            origem = match.group(1).strip().title()
            destino = match.group(2).strip().title()
            
            # Limpa caracteres especiais
            origem = re.sub(r'[^\w\s]', '', origem)
            destino = re.sub(r'[^\w\s]', '', destino)
            
            return origem, destino
    
    return None, None