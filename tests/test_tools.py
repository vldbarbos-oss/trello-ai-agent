from datetime import datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo
import pytest

from agenttaskmanager.normalizer import (
    STATUS_A_FAZER,
    STATUS_EM_ANDAMENTO,
    STATUS_CONCLUIDO,
)


def test_temporal_context_timezone():
    from agenttaskmanager.agent import get_temporal_context

    contexto = get_temporal_context()
    assert isinstance(contexto, str)
    # Deve conter ano/mes/dia hora:min:seg
    assert len(contexto.split()) == 2

    # Verifica se reflete o fuso horário America/Sao_Paulo
    fuso_sp = ZoneInfo("America/Sao_Paulo")
    agora_sp = datetime.now(fuso_sp)
    assert contexto.startswith(agora_sp.strftime("%Y/%m/%d"))


def criar_mock_trello():
    mock_client = MagicMock()
    mock_board = MagicMock()
    mock_board.name = "DIO"

    mock_lista_todo = MagicMock()
    mock_lista_todo.id = "list_1"
    mock_lista_todo.name = "A fazer"

    mock_lista_doing = MagicMock()
    mock_lista_doing.id = "list_2"
    mock_lista_doing.name = "Em andamento"

    mock_lista_done = MagicMock()
    mock_lista_done.id = "list_3"
    mock_lista_done.name = "Concluído"

    mock_card1 = MagicMock()
    mock_card1.id = "card_1"
    mock_card1.name = "Estudar ADK"
    mock_card1.desc = "Aprender Google ADK"
    mock_card1.due = "2026-11-26T02:59:00.000Z"

    mock_card2 = MagicMock()
    mock_card2.id = "card_2"
    mock_card2.name = "Criar Agente"
    mock_card2.desc = "Integrar com Trello"
    mock_card2.due = "2026-11-27T02:59:00.000Z"

    mock_lista_todo.list_cards.return_value = [mock_card1]
    mock_lista_doing.list_cards.return_value = [mock_card2]
    mock_lista_done.list_cards.return_value = []

    mock_board.list_lists.return_value = [
        mock_lista_todo,
        mock_lista_doing,
        mock_lista_done,
    ]
    mock_client.list_boards.return_value = [mock_board]

    return mock_client, mock_board, mock_lista_todo, mock_lista_doing, mock_lista_done, mock_card1, mock_card2


@patch("agenttaskmanager.agent.get_trello_client")
def test_adicionar_tarefa(mock_get_client):
    mock_client, mock_board, mock_todo, _, _, _, _ = criar_mock_trello()
    mock_get_client.return_value = mock_client

    from agenttaskmanager.agent import adicionar_tarefa

    resultado = adicionar_tarefa("Nova Tarefa", "Descricao da tarefa", "2026-11-30")

    # 2026-11-30 às 23:59 no fuso America/Sao_Paulo (UTC-3) vira 2026-12-01T02:59:00.000Z em UTC
    mock_todo.add_card.assert_called_once_with(
        name="Nova Tarefa",
        desc="Descricao da tarefa",
        due="2026-12-01T02:59:00.000Z"
    )
    assert "Nova Tarefa" in resultado
    assert "✅" in resultado


@patch("agenttaskmanager.agent.get_trello_client")
def test_listar_tarefas_todas(mock_get_client):
    mock_client, _, _, _, _, _, _ = criar_mock_trello()
    mock_get_client.return_value = mock_client

    from agenttaskmanager.agent import listar_tarefas

    tarefas = listar_tarefas("todas")
    assert len(tarefas) == 2
    nomes = [t["nome"] for t in tarefas]
    assert "Estudar ADK" in nomes
    assert "Criar Agente" in nomes
    # Verifica se a data UTC de mock_card1 (2026-11-26T02:59:00.000Z) foi convertida para o horário local (25/11/2026 23:59)
    assert tarefas[0]["vencimento"] == "25/11/2026 23:59"


@patch("agenttaskmanager.agent.get_trello_client")
def test_listar_tarefas_filtro_status(mock_get_client):
    mock_client, _, _, _, _, _, _ = criar_mock_trello()
    mock_get_client.return_value = mock_client

    from agenttaskmanager.agent import listar_tarefas

    # Teste com sinônimo 'pendente' -> A fazer
    tarefas_todo = listar_tarefas("pendente")
    assert len(tarefas_todo) == 1
    assert tarefas_todo[0]["nome"] == "Estudar ADK"

    # Teste com sinônimo 'fazendo' -> Em andamento
    tarefas_doing = listar_tarefas("fazendo")
    assert len(tarefas_doing) == 1
    assert tarefas_doing[0]["nome"] == "Criar Agente"

    # Teste com sinônimo 'finalizado' -> Concluído (vazia)
    tarefas_done = listar_tarefas("finalizado")
    assert len(tarefas_done) == 0


@patch("agenttaskmanager.agent.get_trello_client")
def test_mudar_status_tarefa_sucesso(mock_get_client):
    mock_client, _, _, mock_doing, mock_done, mock_card1, _ = criar_mock_trello()
    mock_get_client.return_value = mock_client

    from agenttaskmanager.agent import mudar_status_tarefa

    # Mover "Estudar ADK" para "fazendo" (Em andamento)
    res1 = mudar_status_tarefa("Estudar ADK", "fazendo")
    mock_card1.change_list.assert_called_with(mock_doing.id)
    assert "✅" in res1
    assert "Em andamento" in res1

    # Mover "Estudar ADK" para "concluído"
    res2 = mudar_status_tarefa("Estudar ADK", "concluído")
    mock_card1.change_list.assert_called_with(mock_done.id)
    assert "✅" in res2
    assert "Concluído" in res2


@patch("agenttaskmanager.agent.get_trello_client")
def test_mudar_status_tarefa_invalido(mock_get_client):
    mock_client, _, _, _, _, _, _ = criar_mock_trello()
    mock_get_client.return_value = mock_client

    from agenttaskmanager.agent import mudar_status_tarefa

    res = mudar_status_tarefa("Estudar ADK", "status_inexistente")
    assert "❌" in res
    assert "Status inválido" in res


@patch("agenttaskmanager.agent.get_trello_client")
def test_mudar_status_card_nao_encontrado(mock_get_client):
    mock_client, _, _, _, _, _, _ = criar_mock_trello()
    mock_get_client.return_value = mock_client

    from agenttaskmanager.agent import mudar_status_tarefa

    res = mudar_status_tarefa("Tarefa Fantasma", "feito")
    assert "❌" in res
    assert "não encontrado" in res
