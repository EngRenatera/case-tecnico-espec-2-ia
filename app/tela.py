"""Tela da revendedora.

O `st.session_state` guarda quem está falando, o id da sessão e o
histórico visível. A memória que responde "dele" continua no checkpoint
do Postgres. Cada evento SSE vira um pedaço do `st.write_stream`.
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from collections.abc import Iterator
from pathlib import Path

import httpx
import psycopg

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from app.tools import DATABASE_URL

API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")
LOGO = RAIZ / "app" / "static" / "logo-boticario.svg"
VERDE = "#499d71"


def listar_revendedoras() -> list[tuple[int, str]]:
    with psycopg.connect(DATABASE_URL) as conn:
        return conn.execute(
            """
            SELECT id_revendedora, nm_revendedora
            FROM revendedora
            ORDER BY nm_revendedora
            """
        ).fetchall()


def criar_sessao(id_revendedora: int) -> str:
    id_sessao = str(uuid.uuid4())
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(
            """
            INSERT INTO sessao (id_sessao, id_revendedora)
            VALUES (%(id_sessao)s, %(id_revendedora)s)
            """,
            {"id_sessao": id_sessao, "id_revendedora": id_revendedora},
        )
    return id_sessao


def texto_do_evento(linha: str) -> str | None:
    if not linha.startswith("data: "):
        return None
    return json.loads(linha.removeprefix("data: "))["texto"]


def consultar(id_revendedora: int, id_sessao: str, mensagem: str) -> Iterator[str]:
    try:
        with httpx.Client(timeout=180) as cliente:
            with cliente.stream(
                "POST",
                f"{API_URL}/chat",
                json={
                    "id_revendedora": id_revendedora,
                    "id_sessao": id_sessao,
                    "mensagem": mensagem,
                },
            ) as resposta:
                if resposta.status_code >= 400:
                    yield _detalhe(resposta)
                    return
                veio = False
                for linha in resposta.iter_lines():
                    pedaco = texto_do_evento(linha)
                    if pedaco:
                        veio = True
                        yield pedaco
                if not veio:
                    yield "Sem resposta."
    except httpx.ConnectError:
        yield "A API não está no ar. Suba o uvicorn na porta 8000."


def _detalhe(resposta: httpx.Response) -> str:
    corpo = resposta.read().decode()
    try:
        return str(json.loads(corpo)["detail"])
    except (json.JSONDecodeError, KeyError):
        return corpo or "A API recusou a mensagem."


def _aparencia() -> str:
    return f"""
    <style>
      header[data-testid="stHeader"] {{
        background: {VERDE};
      }}
      [data-testid="stDecoration"] {{
        background: {VERDE};
      }}
      .stAppDeployButton, #MainMenu, footer {{
        visibility: hidden;
      }}
      .marca svg {{
        width: min(420px, 100%);
        height: auto;
        display: block;
        margin: 0.4rem 0 0.8rem;
        overflow: visible;
      }}
      h1 {{
        color: #163028;
      }}
      [data-testid="stChatMessage"]:nth-of-type(odd) {{
        background: #e7f3ec;
        border-radius: 12px;
        padding: 0.2rem 0.4rem;
      }}
    </style>
    """


def main() -> None:
    import streamlit as st

    st.set_page_config(page_title="Assistente da revendedora")
    st.markdown(_aparencia(), unsafe_allow_html=True)
    st.markdown(
        f'<div class="marca">{LOGO.read_text(encoding="utf-8")}</div>',
        unsafe_allow_html=True,
    )
    st.title("Assistente da revendedora")
    st.caption(
        "A tela guarda a revendedora e o histórico visível. "
        "A memória da conversa fica no Postgres, na sessão."
    )

    revendedoras = listar_revendedoras()
    por_nome = {nome: id_revendedora for id_revendedora, nome in revendedoras}
    escolha = st.selectbox("Revendedora", list(por_nome))
    id_revendedora = por_nome[escolha]

    if st.session_state.get("id_revendedora") != id_revendedora:
        st.session_state.id_revendedora = id_revendedora
        st.session_state.id_sessao = criar_sessao(id_revendedora)
        st.session_state.mensagens = []
        st.rerun()

    coluna_sessao, coluna_botao = st.columns([4, 1])
    coluna_sessao.caption(f"Sessão {st.session_state.id_sessao}")
    if coluna_botao.button("Nova sessão", type="primary", use_container_width=True):
        st.session_state.id_sessao = criar_sessao(id_revendedora)
        st.session_state.mensagens = []
        st.rerun()

    for mensagem in st.session_state.mensagens:
        with st.chat_message(mensagem["papel"]):
            st.markdown(mensagem["texto"])

    pergunta = st.chat_input("Escreva sua mensagem")
    if not pergunta:
        return

    st.session_state.mensagens.append({"papel": "user", "texto": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)
    with st.chat_message("assistant"):
        texto = st.write_stream(consultar(id_revendedora, st.session_state.id_sessao, pergunta))
    st.session_state.mensagens.append({"papel": "assistant", "texto": texto})


if __name__ == "__main__":
    main()
