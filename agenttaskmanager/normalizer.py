"""Módulo para normalização de status de tarefas utilizando recursos nativos do Python.

Permite reconhecer variações linguísticas, acentuações, maiúsculas/minúsculas e
sinônimos para as listas do Trello: 'A fazer', 'Em andamento' e 'Concluído'.
"""

import re
import unicodedata
from typing import Optional

# Status canônicos correspondentes aos nomes esperados no Trello
STATUS_A_FAZER = "A fazer"
STATUS_EM_ANDAMENTO = "Em andamento"
STATUS_CONCLUIDO = "Concluído"
STATUS_TODAS = "todas"

# Mapeamento de termos normalizados para cada status canônico
_MAPA_VARIACOES = {
    STATUS_A_FAZER: {
        "a fazer",
        "afazer",
        "pendente",
        "pendentes",
        "to do",
        "todo",
    },
    STATUS_EM_ANDAMENTO: {
        "em andamento",
        "emandamento",
        "em progresso",
        "progresso",
        "fazendo",
        "doing",
        "in progress",
    },
    STATUS_CONCLUIDO: {
        "concluido",
        "finalizado",
        "feito",
        "pronto",
        "done",
        "terminado",
    },
    STATUS_TODAS: {
        "todas",
        "todos",
        "all",
        "*",
    },
}


def remover_acentos(texto: str) -> str:
    """Remove marcas diacríticas/acentuação de uma string usando unicodedata."""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def limpar_texto(texto: str) -> str:
    """Converte para minúsculas, remove acentos e caracteres especiais irrelevantes."""
    sem_acentos = remover_acentos(texto.strip().lower())
    # Mantém letras, dígitos, espaços e asterisco
    substituido = re.sub(r"[^a-z0-9\s\*]", " ", sem_acentos)
    # Reduz espaços múltiplos a um único espaço
    return re.sub(r"\s+", " ", substituido).strip()


def normalizar_status(status: Optional[str]) -> Optional[str]:
    """Normaliza um termo de status para um dos status canônicos.

    Args:
        status: String informada pelo usuário ou extraída do Trello.

    Returns:
        Um dos valores canônicos: STATUS_A_FAZER, STATUS_EM_ANDAMENTO,
        STATUS_CONCLUIDO, STATUS_TODAS, ou None se não reconhecido.
    """
    if not status or not isinstance(status, str):
        return None

    termo_limpo = limpar_texto(status)
    if not termo_limpo:
        return None

    for canonico, variacoes in _MAPA_VARIACOES.items():
        if termo_limpo in variacoes:
            return canonico

    return None
