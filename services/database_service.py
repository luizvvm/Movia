# services/database_service.py
from google.cloud import firestore
import config

try:
    # A autenticação acontece automaticamente através da variável de ambiente
    # GOOGLE_APPLICATION_CREDENTIALS que definimos no .env
    db = firestore.Client(project=config.FIRESTORE_PROJECT_ID)
    print("INFO: Conexão com o Firestore estabelecida com sucesso!")
except Exception as e:
    print(f"ERRO CRÍTICO: Não foi possível conectar ao Firestore. Verifique suas credenciais e o project_id. Erro: {e}")
    db = None

def registrar_interacao(user_id, texto_usuario, intent):
    """
    Função de exemplo para salvar uma interação no Firestore.
    """
    if not db:
        print("ERRO: Conexão com o Firestore não está disponível.")
        return

    try:
        doc_ref = db.collection('interacoes').document()
        doc_ref.set({
            'user_id': user_id,
            'mensagem': texto_usuario,
            'intent': intent,
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        print(f"INFO: Interação do usuário {user_id} registrada.")
    except Exception as e:
        print(f"ERRO: Falha ao registrar interação no Firestore: {e}")