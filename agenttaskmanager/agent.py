"""Agente de Inteligência Artificial para Gerenciamento de Tarefas no Trello.

Projeto educacional desenvolvido para o desafio prático da Digital Innovation One (DIO).
Baseado no projeto de referência:
Digital Innovation One (DIO) - agent-carbon-footprint / agent04
Instrutor responsável: Henrique Eduardo Souza (DIO)
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from google.adk.agents.llm_agent import Agent
from trello import TrelloClient

from .normalizer import (
    normalizar_status,
    STATUS_A_FAZER,
    STATUS_EM_ANDAMENTO,
    STATUS_CONCLUIDO,
    STATUS_TODAS,
)
from .date_utils import (
    converter_para_utc,
    converter_de_utc_para_local,
)

# Carrega variáveis de ambiente do .env
load_dotenv()

# Fuso horário padrão do projeto
FUSO_HORARIO = ZoneInfo("America/Sao_Paulo")
BOARD_NAME_PADRAO = "DIO"


def get_trello_client() -> TrelloClient:
    """Instancia e retorna o cliente do Trello utilizando as variáveis de ambiente."""
    api_key = os.getenv("TRELLO_API_KEY")
    api_secret = os.getenv("TRELLO_API_SECRET")
    token = os.getenv("TRELLO_TOKEN")

    if not api_key or not token:
        raise ValueError(
            "Credenciais do Trello não configuradas. "
            "Defina TRELLO_API_KEY e TRELLO_TOKEN no arquivo .env."
        )

    return TrelloClient(
        api_key=api_key,
        api_secret=api_secret,
        token=token,
    )


def obter_board(client: TrelloClient, board_name: Optional[str] = None):
    """Localiza o quadro no Trello pelo nome (padrão: 'DIO')."""
    alvo = (board_name or os.getenv("TRELLO_BOARD_NAME") or BOARD_NAME_PADRAO).strip().upper()
    boards = client.list_boards()
    for b in boards:
        if b.name.strip().upper() == alvo:
            return b
    raise ValueError(f"Quadro '{alvo}' não encontrado no Trello.")


def get_temporal_context() -> str:
    """Retorna o contexto temporal atual formatado (AAAA/MM/DD HH:MM:SS) no fuso America/Sao_Paulo.
    
    Esta ferramenta deve ser chamada no início da conversa para saudar o usuário informando a data.
    """
    agora = datetime.now(FUSO_HORARIO)
    return agora.strftime("%Y/%m/%d %H:%M:%S")


def adicionar_tarefa(nome_da_task: str, descricao_da_task: str, due_date: str = "") -> str:
    """Cria um cartão na lista 'A fazer' do Trello com nome, descrição e data de vencimento opcional.

    Args:
        nome_da_task: Título ou nome da tarefa a ser criada.
        descricao_da_task: Detalhes ou descrição explicativa da tarefa.
        due_date: Data de entrega/vencimento no formato YYYY-MM-DD (opcional).

    Returns:
        Mensagem de confirmação ou erro.
    """
    try:
        client = get_trello_client()
        board = obter_board(client)
        listas = board.list_lists()

        # Localiza a lista correspondente a 'A fazer' usando a normalização
        minha_lista = next(
            (l for l in listas if normalizar_status(l.name) == STATUS_A_FAZER),
            None,
        )

        if not minha_lista:
            return "❌ Lista 'A fazer' não encontrada no quadro."

        due_utc = converter_para_utc(due_date) if due_date else None

        card = minha_lista.add_card(
            name=nome_da_task,
            desc=descricao_da_task,
            due=due_utc,
        )

        return f"✅ Tarefa '{nome_da_task}' criada com sucesso na lista '{minha_lista.name}' (ID: {card.id})."
    except Exception as e:
        return f"❌ Erro ao adicionar tarefa: {str(e)}"


def listar_tarefas(status: str = "todas") -> List[Dict[str, Any]]:
    """Lista tarefas do quadro Trello, com opção de filtrar por status.

    Args:
        status: Filtro de status desejado. Pode ser 'todas', 'a fazer' (pendente),
                'em andamento' (fazendo) ou 'concluído' (finalizado).
                Aceita variações e acentuações.

    Returns:
        Lista de dicionários contendo os dados das tarefas encontradas.
    """
    try:
        client = get_trello_client()
        board = obter_board(client)
        listas = board.list_lists()

        status_canonico = normalizar_status(status)

        if not status_canonico or status_canonico == STATUS_TODAS:
            listas_filtradas = listas
        else:
            listas_filtradas = [
                l for l in listas if normalizar_status(l.name) == status_canonico
            ]

        tarefas = []
        for lista in listas_filtradas:
            cards = lista.list_cards()
            for card in cards:
                vencimento_br = converter_de_utc_para_local(getattr(card, "due", None))
                tarefas.append(
                    {
                        "nome": card.name,
                        "descricao": card.desc,
                        "vencimento": vencimento_br,
                        "status": lista.name,
                        "id": card.id,
                    }
                )

        return tarefas
    except Exception as e:
        return [{"erro": f"❌ Erro ao listar tarefas: {str(e)}"}]


def mudar_status_tarefa(nome_da_task: str, novo_status: str) -> str:
    """Move um cartão existente no Trello para uma nova lista de acordo com o status informado.

    Args:
        nome_da_task: Nome exato ou aproximado da tarefa que deve ser movida.
        novo_status: Novo status desejado ('a fazer', 'em andamento', 'concluído'
                     ou suas variações como 'pendente', 'fazendo', 'finalizado', etc.).

    Returns:
        Mensagem de sucesso indicando a transição de listas ou mensagem de erro.
    """
    try:
        status_destino = normalizar_status(novo_status)
        if not status_destino or status_destino == STATUS_TODAS:
            return (
                f"❌ Status inválido ('{novo_status}'). "
                f"Opções disponíveis: 'A fazer' (pendente), 'Em andamento' (fazendo) "
                f"ou 'Concluído' (finalizado/feito)."
            )

        client = get_trello_client()
        board = obter_board(client)
        listas = board.list_lists()

        # Encontra a lista de destino no board cujo nome normalizado coincide com o status
        lista_destino = next(
            (l for l in listas if normalizar_status(l.name) == status_destino),
            None,
        )

        if not lista_destino:
            return f"❌ Lista de destino para status '{status_destino}' não encontrada no quadro."

        # Busca o cartão pelo nome em todas as listas
        card_encontrado = None
        lista_origem = None

        termo_busca = nome_da_task.strip().lower()

        for lista in listas:
            cards = lista.list_cards()
            card_encontrado = next(
                (c for c in cards if c.name.strip().lower() == termo_busca),
                None,
            )
            if card_encontrado:
                lista_origem = lista
                break

        if not card_encontrado:
            return f"❌ Card '{nome_da_task}' não encontrado no quadro."

        # Realiza a movimentação do card para a lista de destino
        card_encontrado.change_list(lista_destino.id)
        return f"✅ '{nome_da_task}': {lista_origem.name} → {lista_destino.name}"
    except Exception as e:
        return f"❌ Erro ao mudar status da tarefa: {str(e)}"


# Definição do agente raiz para o Google ADK
root_agent = Agent(
    model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
    name="root_agent",
    description="Agente inteligente para gerenciamento e organização de tarefas no Trello.",
    instruction="""
Você é um agente especialista em organização e gerenciamento de tarefas integrado ao Trello.

Comportamento inicial obrigatório:
1. Assim que a conversa começar, você DEVE saudar o usuário e informá-lo da data e hora atual obtida através da ferramenta `get_temporal_context` (fuso horário America/Sao_Paulo).
2. Pergunte ao usuário quais tarefas ele planeja realizar no dia de hoje.
3. Conforme o usuário for informando, crie os cartões no Trello usando a ferramenta `adicionar_tarefa` (informando nome, descrição e data de vencimento se houver).
4. Em seguida, pergunte proativamente se ele tem mais alguma tarefa para adicionar, repetindo o processo até que ele diga que finalizou a inserção.

Suas capacidades e ferramentas disponíveis:
- `get_temporal_context`: Obtém a data e hora atual em America/Sao_Paulo para situar as atividades.
- `adicionar_tarefa`: Cria um cartão no Trello na lista "A fazer" com nome, descrição e vencimento.
- `listar_tarefas`: Lista todas as tarefas ou filtra por status ("A fazer", "Em andamento", "Concluído", ou termos como "pendente", "fazendo", "finalizado").
- `mudar_status_tarefa`: Move cartões entre as listas ("A fazer", "Em andamento" e "Concluído"), compreendendo linguagem natural, variações e sinônimos (ex: mover para fazendo/em progresso, ou marcar como concluído/finalizado/feito).

Mantenha sempre uma comunicação clara, organizada, prestativa e objetiva em português.
""",
    tools=[get_temporal_context, adicionar_tarefa, listar_tarefas, mudar_status_tarefa],
)
