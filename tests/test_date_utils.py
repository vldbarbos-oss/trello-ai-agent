import pytest
from datetime import datetime
from zoneinfo import ZoneInfo
from agenttaskmanager.date_utils import (
    converter_para_utc,
    converter_de_utc_para_local,
    FUSO_SP,
)


def test_converter_para_utc_vazio():
    assert converter_para_utc(None) is None
    assert converter_para_utc("") is None
    assert converter_para_utc("   ") is None


def test_converter_para_utc_sem_horario_padrao_23h59():
    # 25/11/2026 sem horário deve assumir 23:59 local (UTC-3) -> 26/11/2026 02:59:00 UTC
    res_iso = converter_para_utc("2026-11-25")
    assert res_iso == "2026-11-26T02:59:00.000Z"

    # Formato brasileiro DD/MM/AAAA
    res_br = converter_para_utc("25/11/2026")
    assert res_br == "2026-11-26T02:59:00.000Z"


def test_converter_para_utc_com_horario():
    # 25/11/2026 15:30 local (UTC-3) -> 25/11/2026 18:30:00 UTC
    res = converter_para_utc("2026-11-25 15:30")
    assert res == "2026-11-25T18:30:00.000Z"

    res_sec = converter_para_utc("2026-11-25 15:30:45")
    assert res_sec == "2026-11-25T18:30:45.000Z"

    res_br = converter_para_utc("25/11/2026 15:30")
    assert res_br == "2026-11-25T18:30:00.000Z"


def test_converter_de_utc_para_local():
    assert converter_de_utc_para_local(None) is None
    assert converter_de_utc_para_local("") is None

    # Trello retorna 2026-11-26T02:59:00.000Z -> deve converter para 25/11/2026 23:59
    local_str = converter_de_utc_para_local("2026-11-26T02:59:00.000Z")
    assert local_str == "25/11/2026 23:59"

    # 18:30 UTC -> 15:30 local
    local_str2 = converter_de_utc_para_local("2026-11-25T18:30:00.000Z")
    assert local_str2 == "25/11/2026 15:30"
