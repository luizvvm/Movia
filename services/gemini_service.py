# services/gemini_service.py
import json
import google.generativeai as genai
import config

try:
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")
    print("INFO: Modelo Gemini inicializado com sucesso!")
except Exception as e:
    print(f"ERRO CRÍTICO: Falha ao inicializar o modelo Gemini. Verifique a GEMINI_API_KEY. Erro: {e}")
    model = None

# services/gemini_service.py
import json

def get_intent(contexto_completo):
    """
    Analisa a mensagem do usuário no contexto do histórico,
    retorna intenção, parâmetros e novo resumo.
    """
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
        # Exemplo genérico de chamada ao Gemini (ajuste ao seu client real):
        resposta = model.generate_content(prompt)  
        cleaned_response = resposta.text.strip().replace('```json', '').replace('```', '').strip()
        dados = json.loads(cleaned_response)
        return dados
    except Exception as e:
        print(f"ERRO em get_intent: {e}")
        return {
            "intent": "conversa_geral",
            "parameters": {},
            "novo_resumo": contexto_completo[:300]  # fallback simples
        }
    
