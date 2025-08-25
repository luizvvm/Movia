# services/database_service.py
from google.cloud import firestore
import config

try:
    db = firestore.Client(project=config.FIRESTORE_PROJECT_ID)
    print("INFO: Conexão com o Firestore estabelecida com sucesso!")
except Exception as e:
    print(f"ERRO CRÍTICO: Não foi possível conectar ao Firestore. Erro: {e}")
    db = None


def carregar_interacoes_usuario(user_id, limit=50):
    """
    Retorna as interações de um usuário específico, ordenadas por data (mais recente primeiro).
    """
    if not db:
        print("ERRO: Conexão com o Firestore não está disponível.")
        return []

    try:
        interacoes_ref = db.collection('interacoes') \
            .where('user_id', '==', user_id) \
            .order_by('timestamp', direction=firestore.Query.DESCENDING) \
            .limit(limit)

        docs = interacoes_ref.stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        print(f"ERRO: Não foi possível carregar interações do usuário {user_id}: {e}")
        return []


def carregar_resumo_usuario(user_id):
    """
    Retorna o resumo acumulado do histórico de um usuário.
    """
    if not db:
        return ""

    try:
        doc_ref = db.collection("resumos").document(user_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict().get("resumo", "")
        return ""
    except Exception as e:
        print(f"ERRO: Não foi possível carregar resumo do usuário {user_id}: {e}")
        return ""


def atualizar_resumo_usuario(user_id, novo_resumo):
    """
    Atualiza o resumo acumulado do histórico de um usuário.
    """
    if not db:
        return

    try:
        db.collection("resumos").document(user_id).set({
            "user_id": user_id,
            "resumo": novo_resumo,
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        print(f"INFO: Resumo do usuário {user_id} atualizado.")
    except Exception as e:
        print(f"ERRO: Não foi possível atualizar resumo do usuário {user_id}: {e}")


def registrar_interacao(user_id, texto_usuario, intent):
    """
    Registra uma interação no Firestore e mantém no máximo 50 interações por usuário.
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
            print(f"INFO: Interações antigas do usuário {user_id} foram removidas.")

    except Exception as e:
        print(f"ERRO: Falha ao registrar interação no Firestore: {e}")