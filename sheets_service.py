# sheets_service.py

import gspread
import pandas as pd
from datetime import datetime
import os
# A oauth2client pode ser uma dependência do gspread, vamos garantir que está disponível
from oauth2client.service_account import ServiceAccountCredentials 

# --- NOVO Bloco de Autenticação com Escopos Explícitos ---
try:
    # AS LINHAS QUE FALTAVAM ESTÃO AQUI:
    # Define explicitamente as permissões que nossa aplicação precisa.
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    # Agora a variável SCOPES existe e pode ser usada na linha abaixo
    creds = ServiceAccountCredentials.from_json_keyfile_name('google_credentials.json', SCOPES)
    gc = gspread.authorize(creds)
    
    # O resto do código continua igual
    SPREADSHEET_NAME = os.getenv("GOOGLE_SHEET_NAME")
    sh = gc.open(SPREADSHEET_NAME)
    
    print("INFO: Autenticado com Google Sheets com sucesso!")

except gspread.exceptions.SpreadsheetNotFound:
    SPREADSHEET_NAME = os.getenv("GOOGLE_SHEET_NAME")
    print(f"ERRO CRÍTICO: Planilha com o nome '{SPREADSHEET_NAME}' não foi encontrada.")
    print("VERIFIQUE: 1) O nome no arquivo .env está 100% correto? 2) A planilha foi compartilhada como 'Editor' com o e-mail de serviço?")
    sh = None
except FileNotFoundError:
    print("ERRO CRÍTICO: Arquivo 'google_credentials.json' não encontrado.")
    sh = None
except NameError:
    print("ERRO CRÍTICO: A variável 'SCOPES' não foi definida. Verifique o bloco de autenticação no arquivo sheets_service.py.")
    sh = None
except Exception as e:
    print(f"ERRO CRÍTICO: Ocorreu um erro inesperado na conexão com o Google Sheets. Erro: {e}")
    sh = None
# --- Fim do Bloco de Autenticação ---


def get_user_sheet(user_id):
    """
    Garante que uma aba (worksheet) para o usuário exista e a retorna.
    Se a aba não existir, ela é criada com os cabeçalhos corretos. 
    """
    if not sh:
        raise ConnectionError("A conexão com a planilha principal falhou na inicialização.")
    
    # O user_id do WhatsApp vem como "whatsapp:+5521..."
    # O nome da aba não pode conter ':', então o removemos.
    safe_user_id = user_id.replace('whatsapp:', '')

    try:
        # Tenta encontrar a aba pelo ID do usuário
        worksheet = sh.worksheet(safe_user_id)
    except gspread.exceptions.WorksheetNotFound:
        # Se não encontrar, cria uma nova aba para este usuário
        print(f"INFO: Criando nova aba para o usuário {safe_user_id}")
        worksheet = sh.add_worksheet(title=safe_user_id, rows="100", cols="6")
        # Adiciona os cabeçalhos na nova aba
        headers = ["TaskID", "Descricao", "DataCriacao", "Prazo", "Status", "Prioridade"]
        worksheet.append_row(headers)
        
    return worksheet


def add_task_to_sheet(user_id, task_description):
    """
    Adiciona uma nova tarefa à planilha do usuário. [cite: 669, 1191]
    """
    try:
        worksheet = get_user_sheet(user_id)
        
        # Gera um ID simples para a tarefa baseado no número de linhas
        num_rows = len(worksheet.get_all_values())
        task_id = f"T{num_rows}"
        
        creation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Define a nova linha com os dados da tarefa
        new_row = [task_id, task_description, creation_date, "", "Pendente", ""]
        worksheet.append_row(new_row)
        
        print(f"INFO: Tarefa '{task_description}' adicionada para o usuário {user_id}")
        return task_id
        
    except Exception as e:
        print(f"ERRO ao adicionar tarefa para {user_id}: {e}")
        return None


def get_tasks_from_sheet(user_id, status_filter="Pendente"):
    """
    Lista as tarefas de um usuário, com um filtro de status opcional. [cite: 669, 1198]
    """
    try:
        worksheet = get_user_sheet(user_id)
        # get_all_records() convenientemente transforma a planilha em uma lista de dicionários
        all_tasks = worksheet.get_all_records()
        
        if status_filter:
            # Filtra a lista para retornar apenas as tarefas com o status desejado
            filtered_tasks = [task for task in all_tasks if task.get('Status') == status_filter]
            return filtered_tasks
            
        return all_tasks
        
    except Exception as e:
        print(f"ERRO ao listar tarefas para {user_id}: {e}")
        return []
    
def update_task_status(user_id, task_id, new_status="Concluída"):
    """Encontra uma tarefa pelo seu ID e atualiza o status dela."""
    try:
        worksheet = get_user_sheet(user_id)
        cell = worksheet.find(task_id) # Encontra a célula com o TaskID (ex: "T1")
        
        if not cell:
            print(f"ERRO: TaskID '{task_id}' não encontrado para o usuário {user_id}")
            return False
            
        # A coluna 'Status' é a 5ª coluna (coluna E).
        # Atualizamos a célula na mesma linha (cell.row) e na coluna 5.
        worksheet.update_cell(cell.row, 5, new_status)
        print(f"INFO: Status da tarefa {task_id} atualizado para {new_status} para o usuário {user_id}")
        return True
        
    except Exception as e:
        print(f"ERRO ao atualizar status da tarefa para {user_id}: {e}")
        return False