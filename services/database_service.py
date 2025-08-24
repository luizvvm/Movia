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

def carregar_interacoes_usuario(user_id):
    """
    Retorna as interações de um usuário específico, ordenadas por data (mais recente primeiro).
    """
    if not db:
        print("ERRO: Conexão com o Firestore não está disponível.")
        return []

    try:
        interacoes_ref = db.collection('interacoes') \
            .where('user_id', '==', user_id) \
            .order_by('timestamp', direction=firestore.Query.DESCENDING)

        docs = interacoes_ref.stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        print(f"ERRO: Não foi possível carregar interações do usuário {user_id}: {e}")
        return []

def registrar_interacao(user_id, texto_usuario, intent):
    """
    Registra uma interação no Firestore, mantendo no máximo 50 interações por usuário.
    """
    if not db:
        print("ERRO: Conexão com o Firestore não está disponível.")
        return

    try:
        # Adiciona a nova interação
        nova_interacao_ref = db.collection('interacoes').document()
        nova_interacao_ref.set({
            'user_id': user_id,
            'mensagem': texto_usuario,
            'intent': intent,
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        print(f"INFO: Interação do usuário {user_id} registrada.")

        # Verifica a quantidade de interações existentes
        interacoes_ref = db.collection('interacoes') \
            .where('user_id', '==', user_id) \
            .order_by('timestamp', direction=firestore.Query.DESCENDING)

        interacoes = list(interacoes_ref.stream())

        # Se houver mais de 50, deletar as mais antigas
        if len(interacoes) > 50:
            for doc in interacoes[50:]:
                doc.reference.delete()
            print(f"INFO: Interações antigas do usuário {user_id} foram removidas para manter o limite de 50.")
    except Exception as e:
        print(f"ERRO: Falha ao registrar interação no Firestore: {e}")