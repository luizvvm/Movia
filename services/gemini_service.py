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

def get_intent(texto_usuario):
    """
    Analisa a mensagem do usuário e retorna a intenção e os parâmetros.
    """
    if not model:
        return {"intent": "erro_ia", "parameters": {}, "response_to_user": "Estou com um probleminha técnico. Tente novamente em um instante."}
    
    prompt = f"""
    Você é a "Mob.IA", uma assistente de mobilidade urbana para o Rio de Janeiro.
    Sua personalidade é prestativa, clara e confiável.
    Seu objetivo é analisar a mensagem do usuário e identificar a intenção principal para rotear a solicitação.

    As intenções possíveis são:
    - "consultar_rota": O usuário quer saber como ir de um ponto A para um ponto B. Extraia a origem e o destino.
    - "consultar_seguranca": O usuário está perguntando sobre a segurança de um local ou linha de ônibus. Extraia o local ou linha.
    - "consultar_sustentabilidade": O usuário quer uma rota com menor emissão de CO2 ou informações sobre transportes ecológicos.
    - "conversa_geral": Qualquer outra interação (saudações, perguntas genéricas, etc.).

    MENSAGEM DO USUÁRIO: "{texto_usuario}"

    Responda SEMPRE no seguinte formato JSON:
    {{
      "intent": "string",
      "parameters": {{
        "origem": "string (opcional)",
        "destino": "string (opcional)",
        "local": "string (opcional)"
      }}
    }}

    Exemplos:
    1. MENSAGEM: "bom dia"
       RESPOSTA: {{"intent": "conversa_geral", "parameters": {{}}}}

    2. MENSAGEM: "como faço pra ir da Central do Brasil até Copacabana?"
       RESPOSTA: {{"intent": "consultar_rota", "parameters": {{"origem": "Central do Brasil", "destino": "Copacabana"}}}}

    3. MENSAGEM: "a linha 483 é perigosa à noite?"
       RESPOSTA: {{"intent": "consultar_seguranca", "parameters": {{"local": "linha 483 noite"}}}}

    4. MENSAGEM: "qual o jeito mais ecológico de chegar no Jardim Botânico?"
       RESPOSTA: {{"intent": "consultar_sustentabilidade", "parameters": {{"destino": "Jardim Botânico"}}}}
    """

    try:
        response = model.generate_content(prompt)
        # Limpando a resposta para garantir que seja um JSON válido
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '').strip()
        parsed_json = json.loads(cleaned_response)
        return parsed_json
    except (json.JSONDecodeError, Exception) as e:
        print(f"ERRO: Falha ao processar resposta do Gemini: {e}. Resposta recebida: {response.text}")
        return {"intent": "conversa_geral", "parameters": {}}