"""Endpoint do chat.

Confere a dona da sessão, espera a frase inteira do grafo, mascara e só
então corta em eventos SSE. A primeira palavra não sai antes disso.
"""

from __future__ import annotations

import json
from collections.abc import Iterator

import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.graph import abrir_grafo, invocar
from app.guardrails import mascarar_saida
from app.tools import DATABASE_URL

app = FastAPI(title="Assistente da revendedora")


class PedidoChat(BaseModel):
    id_revendedora: int = Field(gt=0)
    id_sessao: str = Field(min_length=1)
    mensagem: str = Field(min_length=1)


def conferir_sessao(id_sessao: str, id_revendedora: int) -> None:
    """Abre a sessão na primeira mensagem. Recusa se já for de outra pessoa."""
    with psycopg.connect(DATABASE_URL) as conn:
        dono = conn.execute(
            "SELECT id_revendedora FROM sessao WHERE id_sessao = %(id_sessao)s",
            {"id_sessao": id_sessao},
        ).fetchone()
        if dono is None:
            try:
                conn.execute(
                    """
                    INSERT INTO sessao (id_sessao, id_revendedora)
                    VALUES (%(id_sessao)s, %(id_revendedora)s)
                    """,
                    {"id_sessao": id_sessao, "id_revendedora": id_revendedora},
                )
            except psycopg.errors.ForeignKeyViolation:
                raise HTTPException(status_code=404, detail="Revendedora não encontrada.")
            return
        if dono[0] != id_revendedora:
            raise HTTPException(status_code=403, detail="Sessão de outra revendedora.")


def invocar_mensagem(id_revendedora: int, id_sessao: str, mensagem: str) -> str:
    with abrir_grafo() as grafo:
        estado = invocar(
            grafo,
            id_revendedora=id_revendedora,
            id_sessao=id_sessao,
            mensagem=mensagem,
        )
    return estado.get("resposta", "")


def fatiar(texto: str) -> list[str]:
    palavras = texto.split()
    if not palavras:
        return []
    return [palavra + " " for palavra in palavras[:-1]] + [palavras[-1]]


def eventos(texto: str) -> Iterator[str]:
    for pedaco in fatiar(texto):
        yield f"data: {json.dumps({'texto': pedaco}, ensure_ascii=False)}\n\n"


@app.post("/chat")
def chat(corpo: PedidoChat) -> StreamingResponse:
    conferir_sessao(corpo.id_sessao, corpo.id_revendedora)
    resposta = mascarar_saida(
        invocar_mensagem(corpo.id_revendedora, corpo.id_sessao, corpo.mensagem)
    )
    return StreamingResponse(eventos(resposta), media_type="text/event-stream")
