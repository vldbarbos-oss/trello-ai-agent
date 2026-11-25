import pytest
from agenttaskmanager.normalizer import (
    normalizar_status,
    STATUS_A_FAZER,
    STATUS_EM_ANDAMENTO,
    STATUS_CONCLUIDO,
    STATUS_TODAS,
)


def test_normalizar_a_fazer_variacoes():
    casos = [
        "A fazer",
        "a fazer",
        "A FAZER",
        "A Fazer",
        "pendente",
        "PENDENTE",
        "Pendente",
        "pendentes",
        "to do",
        "TODO",
        "to-do",
    ]
    for caso in casos:
        assert normalizar_status(caso) == STATUS_A_FAZER, f"Falha no caso: {caso}"


def test_normalizar_em_andamento_variacoes():
    casos = [
        "Em andamento",
        "em andamento",
        "EM ANDAMENTO",
        "em progresso",
        "EM PROGRESSO",
        "Em Progresso",
        "progresso",
        "fazendo",
        "FAZENDO",
        "Fazendo",
        "doing",
        "in progress",
    ]
    for caso in casos:
        assert normalizar_status(caso) == STATUS_EM_ANDAMENTO, f"Falha no caso: {caso}"


def test_normalizar_concluido_variacoes():
    casos = [
        "Concluído",
        "concluído",
        "CONCLUÍDO",
        "concluido",
        "CONCLUIDO",
        "Concluido",
        "finalizado",
        "FINALIZADO",
        "Finalizado",
        "feito",
        "FEITO",
        "Feito",
        "pronto",
        "PRONTO",
        "done",
        "DONE",
        "terminado",
    ]
    for caso in casos:
        assert normalizar_status(caso) == STATUS_CONCLUIDO, f"Falha no caso: {caso}"


def test_normalizar_todas():
    casos = ["todas", "TODAS", "todos", "all", "*"]
    for caso in casos:
        assert normalizar_status(caso) == STATUS_TODAS, f"Falha no caso: {caso}"


def test_normalizar_status_com_espacos_e_caracteres_especiais():
    assert normalizar_status("  a   fazer  ") == STATUS_A_FAZER
    assert normalizar_status("  concluído! ") == STATUS_CONCLUIDO
    assert normalizar_status("\nem andamento\t") == STATUS_EM_ANDAMENTO


def test_normalizar_status_invalido():
    assert normalizar_status("desconhecido") is None
    assert normalizar_status("") is None
    assert normalizar_status(None) is None
    assert normalizar_status("qualquer outra coisa") is None
