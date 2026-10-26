"""O 403 sai antes do grafo. O SSE só carrega texto já mascarado."""

import json
import uuid

import psycopg
from fastapi.testclient import TestClient

from app.guardrails import mascarar_saida
from app.main import app
from app.tools import DATABASE_URL


def _id(nome: str) -> int:
    with psycopg.connect(DATABASE_URL) as conn:
        return conn.execute(
            "SELECT id_revendedora FROM revendedora WHERE nm_revendedora = %s",
            (nome,),
        ).fetchone()[0]


def _juntar(corpo: str) -> str:
    eventos = [linha for linha in corpo.splitlines() if linha.startswith("data: ")]
    return "".join(json.loads(linha.removeprefix("data: "))["texto"] for linha in eventos)


def test_sessao_da_maria_usada_pela_ana_responde_403(monkeypatch):
    def proibido(*args, **kwargs):
        raise AssertionError("o grafo não deveria rodar")

    monkeypatch.setattr("app.main.invocar_mensagem", proibido)
    sessao = f"fase6-{uuid.uuid4().hex}"
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(
            "INSERT INTO sessao (id_sessao, id_revendedora) VALUES (%s, %s)",
            (sessao, _id("Maria Lima")),
        )

    with TestClient(app) as cliente:
        resposta = cliente.post(
            "/chat",
            json={
                "id_revendedora": _id("Ana Souza"),
                "id_sessao": sessao,
                "mensagem": "oi",
            },
        )

    assert resposta.status_code == 403
    assert resposta.json()["detail"] == "Sessão de outra revendedora."


def test_sse_mascara_a_frase_inteira_e_entrega_em_partes(monkeypatch):
    bruto = "Seu CPF é 123.456.789-09, ok?"
    monkeypatch.setattr("app.main.invocar_mensagem", lambda *args, **kwargs: bruto)

    with TestClient(app) as cliente:
        resposta = cliente.post(
            "/chat",
            json={
                "id_revendedora": _id("Ana Souza"),
                "id_sessao": f"fase6-{uuid.uuid4().hex}",
                "mensagem": "oi",
            },
        )

    assert resposta.status_code == 200
    assert resposta.headers["content-type"].startswith("text/event-stream")
    assert "123.456.789-09" not in resposta.text
    eventos = [linha for linha in resposta.text.splitlines() if linha.startswith("data: ")]
    assert len(eventos) > 1
    assert _juntar(resposta.text) == mascarar_saida(bruto)
