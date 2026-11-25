"""Módulo de utilitários de data e fuso horário para integração com o Trello.

Lida com a conversão de horários locais (America/Sao_Paulo) para UTC
ao enviar para a API do Trello, e de UTC para horário local ao exibir.
"""

from datetime import datetime, timezone
from typing import Optional, Union
from zoneinfo import ZoneInfo
import re

FUSO_SP = ZoneInfo("America/Sao_Paulo")


def converter_para_utc(data_str: Optional[str]) -> Optional[str]:
    """Converte uma data informada no fuso local (America/Sao_Paulo) para UTC no formato ISO 8601.

    Regras:
    - Se data_str for vazia ou None, retorna None.
    - Se não houver horário especificado, adota 23:59:00 no fuso local.
    - Formatos aceitos:
      * YYYY-MM-DD
      * DD/MM/YYYY
      * YYYY-MM-DD HH:MM[:SS] ou YYYY-MM-DDTHH:MM[:SS]
      * DD/MM/YYYY HH:MM[:SS] ou DD/MM/YYYYTHH:MM[:SS]
    - Retorna a string formatada em ISO 8601 UTC: 'YYYY-MM-DDTHH:MM:SS.000Z'.
    """
    if not data_str or not isinstance(data_str, str):
        return None

    texto = data_str.strip()
    if not texto:
        return None

    # 1. Formato brasileiro DD/MM/YYYY com ou sem hora
    match_br = re.match(
        r"^(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})(?:[ T](\d{1,2}):(\d{1,2})(?::(\d{1,2}))?)?$",
        texto,
    )
    if match_br:
        dia, mes, ano, hora, minuto, segundo = match_br.groups()
        h = int(hora) if hora is not None else 23
        m = int(minuto) if minuto is not None else 59
        s = int(segundo) if segundo is not None else 0
        dt_local = datetime(int(ano), int(mes), int(dia), h, m, s, tzinfo=FUSO_SP)
        dt_utc = dt_local.astimezone(timezone.utc)
        return dt_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    # 2. Formato ISO YYYY-MM-DD com ou sem hora
    match_iso = re.match(
        r"^(\d{4})[/.-](\d{1,2})[/.-](\d{1,2})(?:[ T](\d{1,2}):(\d{1,2})(?::(\d{1,2}))?)?$",
        texto,
    )
    if match_iso:
        ano, mes, dia, hora, minuto, segundo = match_iso.groups()
        h = int(hora) if hora is not None else 23
        m = int(minuto) if minuto is not None else 59
        s = int(segundo) if segundo is not None else 0
        dt_local = datetime(int(ano), int(mes), int(dia), h, m, s, tzinfo=FUSO_SP)
        dt_utc = dt_local.astimezone(timezone.utc)
        return dt_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    # 3. Fallback: tentar datetime.fromisoformat
    try:
        normalizado = texto.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalizado)
        if dt.tzinfo is None:
            # Assume horário local com 23:59 se só tinha data
            h = dt.hour if dt.hour != 0 or dt.minute != 0 else 23
            m = dt.minute if dt.hour != 0 or dt.minute != 0 else 59
            dt = dt.replace(hour=h, minute=m, tzinfo=FUSO_SP)
        dt_utc = dt.astimezone(timezone.utc)
        return dt_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    except Exception:
        return texto


def converter_de_utc_para_local(data_utc: Union[str, datetime, None]) -> Optional[str]:
    """Converte uma data UTC vinda do Trello para o fuso local (America/Sao_Paulo).

    Retorna formatada como 'DD/MM/AAAA HH:MM'.
    """
    if not data_utc:
        return None

    if isinstance(data_utc, datetime):
        if data_utc.tzinfo is None:
            data_utc = data_utc.replace(tzinfo=timezone.utc)
        dt_local = data_utc.astimezone(FUSO_SP)
        return dt_local.strftime("%d/%m/%Y %H:%M")

    texto = str(data_utc).strip()
    if not texto:
        return None

    try:
        normalizado = texto.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalizado)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt_local = dt.astimezone(FUSO_SP)
        return dt_local.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return texto
