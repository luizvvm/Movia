# preferences_module.py
from services import database_service

def processar_preferencia(mensagem, user_id):
    mensagem = mensagem.lower()
    
    if 'rápida' in mensagem or 'rápido' in mensagem:
        return filtrar_rotas_mais_rapidas(user_id)
    elif 'segura' in mensagem or 'seguro' in mensagem:
        return filtrar_rotas_mais_seguras(user_id)
    elif 'econômica' in mensagem or 'econômico' in mensagem or 'barata' in mensagem or 'barato' in mensagem:
        return filtrar_rotas_mais_economicas(user_id)
    elif 'sustentável' in mensagem:
        return filtrar_rotas_mais_sustentaveis(user_id)
    elif 'acessível' in mensagem:
        return filtrar_rotas_mais_acessiveis(user_id)
    elif 'todas' in mensagem:
        return mostrar_todas_rotas(user_id)
    else:
        return "❌ Não entendi sua preferência. Digite: rápida, segura, econômica, sustentável ou acessível"

def filtrar_rotas_mais_rapidas(user_id):
    # Buscar rotas do usuário e retornar a mais rápida
    rotas = database_service.carregar_rotas_usuario(user_id)
    if rotas:
        return "🚀 *Rota mais rápida selecionada!*\n\n(Detalhes da rota mais rápida aqui)"
    return "❌ Não encontrei rotas salvas para filtrar."

def filtrar_rotas_mais_seguras(user_id):
    return "🛡️ *Rota mais segura selecionada!*\n\nRotas com melhor iluminação e movimento."

def filtrar_rotas_mais_economicas(user_id):
    return "💰 *Rota mais econômica selecionada!*\n\nMenor custo com transporte."

def filtrar_rotas_mais_sustentaveis(user_id):
    return "🌿 *Rota mais sustentável selecionada!*\n\nMenor impacto ambiental."

def filtrar_rotas_mais_acessiveis(user_id):
    return "🤝 *Rota mais acessível selecionada!*\n\nMelhor para pessoas com mobilidade reduzida."

def mostrar_todas_rotas(user_id):
    rotas = database_service.carregar_rotas_usuario(user_id)
    if rotas:
        return "📋 *Todas as rotas disponíveis:*\n\n(Lista completa de rotas aqui)"
    return "❌ Não encontrei rotas salvas."