"""Regras determinísticas. Não chamam o modelo.

A entrada recusa margem de outra pessoa, ranking de margem e pedido de
CPF, telefone ou e-mail. A saída apaga esses dados se o redator os
escrever. A query da fase 3 continua sendo o limite que a tool respeita.
"""

from __future__ import annotations

import re
import unicodedata

import psycopg

from app.tools import DATABASE_URL

_PEDIDO_DE_DADO_PESSOAL = ("cpf", "telefone", "celular", "e-mail", "email", "e mail")
_DESVIO = ("ignore as regras", "ignore as instrucoes")
_MARGEM_ALHEIA = (
    "liste as margens",
    "listar as margens",
    "lista de margens",
    "todas as margens",
    "as margens",
    "quem tem margem",
    "margem acima",
    "margens acima",
    "maior margem",
    "menor margem",
    "ranking",
)
_CPF = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")
_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_TELEFONE = re.compile(r"(?:\+55\s?)?(?:\(\d{2}\)|\d{2})[\s-]?(?:9[\s-]?)?\d{4,5}-\d{4}\b")
_CPF_SEM_MASCARA = re.compile(r"\b\d{11}\b")


def _sem_acento(texto: str) -> str:
    base = unicodedata.normalize("NFD", texto.lower())
    return "".join(letra for letra in base if unicodedata.category(letra) != "Mn")


def _nomes_alheios(id_revendedora: int) -> list[str]:
    with psycopg.connect(DATABASE_URL) as conn:
        linhas = conn.execute(
            """
            SELECT nm_revendedora
            FROM revendedora
            WHERE id_revendedora <> %(id_revendedora)s
            """,
            {"id_revendedora": id_revendedora},
        ).fetchall()
    nomes: list[str] = []
    for (nome,) in linhas:
        limpo = _sem_acento(nome)
        nomes.append(limpo)
        nomes.append(limpo.split()[0])
    return nomes


def margem_da_sessao(mensagem: str) -> bool:
    """A frase pede a margem de quem está na sessão. O modelo não decide isso."""
    frase = _sem_acento(mensagem)
    if "margem" not in frase:
        return False
    return any(pista in frase for pista in ("minha", "meu", "propria"))


def entrada_bloqueada(mensagem: str, id_revendedora: int) -> bool:
    frase = _sem_acento(mensagem)
    if any(pista in frase for pista in _PEDIDO_DE_DADO_PESSOAL):
        return True
    if any(pista in frase for pista in _DESVIO):
        return True
    if "margem" not in frase:
        return False
    if any(pista in frase for pista in _MARGEM_ALHEIA):
        return True
    return any(
        re.search(rf"\b{re.escape(nome)}\b", frase) is not None
        for nome in _nomes_alheios(id_revendedora)
    )


def mascarar_saida(texto: str) -> str:
    limpo = _CPF.sub("[cpf]", texto)
    limpo = _EMAIL.sub("[e-mail]", limpo)
    limpo = _TELEFONE.sub("[telefone]", limpo)
    return _CPF_SEM_MASCARA.sub("[cpf]", limpo)
