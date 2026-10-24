"""Grafo do assistente.

Cada mensagem entra num state, o roteador escolhe uma aresta e o
PostgresSaver grava o state na chave da sessão. O modelo classifica a
intenção. O código chama a tool e guarda o pedido em foco.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Callable
from contextlib import contextmanager
from typing import Annotated, Iterator, Literal

import psycopg
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel, ValidationError
from typing_extensions import TypedDict

from app.rag import buscar_catalogo
from app.tools import DATABASE_URL, consultar_estoque, consultar_minha_margem, consultar_pedidos

Intencao = Literal["catalogo", "pedido", "ambos", "conversa", "bloqueado"]
RECUSA = "Não consigo consultar dados de outra revendedora."
LLM_MODEL = os.environ.get("LLM_MODEL", "qwen2.5:7b-instruct")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

_REFERENCIA_AO_PEDIDO = (
    "dele",
    "dela",
    "desse",
    "dessa",
    "nele",
    "nela",
    "esse pedido",
    "transportadora",
)


class Estado(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    id_revendedora: int
    id_sessao: str
    intencao: Intencao
    id_pedido_em_foco: int | None
    trechos_catalogo: list[str]
    linhas_transacionais: list
    resposta: str


class IntencaoModelo(BaseModel):
    intencao: Intencao


def interpretar_intencao(texto: str) -> Intencao:
    """Aceita o JSON do modelo e recusa qualquer intenção fora do contrato."""
    candidato = texto.strip()
    if candidato.startswith("```"):
        candidato = re.sub(r"^```(?:json)?", "", candidato).strip()
        candidato = re.sub(r"```$", "", candidato).strip()
    inicio = candidato.find("{")
    fim = candidato.rfind("}")
    if inicio < 0 or fim < inicio:
        raise ValueError("O modelo não devolveu um JSON")
    return IntencaoModelo.model_validate(json.loads(candidato[inicio : fim + 1])).intencao


def escolher_consulta(texto: str, id_pedido_em_foco: int | None) -> str:
    """Decide a tool dentro do ramo transacional, sem um segundo loop do modelo."""
    frase = texto.lower()
    if "margem" in frase:
        return "margem"
    if any(p in frase for p in ("estoque", "disponív", "disponiv", "saldo")):
        return "estoque"
    if id_pedido_em_foco is not None and any(p in frase for p in _REFERENCIA_AO_PEDIDO):
        return "pedido_em_foco"
    return "ultimo_pedido"


def produto_citado(texto: str) -> str | None:
    with psycopg.connect(DATABASE_URL) as conn:
        nomes = conn.execute(
            "SELECT nm_produto FROM produto ORDER BY length(nm_produto) DESC"
        ).fetchall()
    frase = texto.lower()
    for (nome,) in nomes:
        if nome.lower() in frase:
            return nome
    return None


def _ultima_mensagem(state: Estado) -> str:
    conteudo = state["messages"][-1].content
    if isinstance(conteudo, str):
        return conteudo
    return str(conteudo)


def _montar_contexto(state: Estado) -> str:
    partes: list[str] = []
    if state.get("trechos_catalogo"):
        partes.append("Catálogo:\n" + "\n---\n".join(state["trechos_catalogo"]))
    if state.get("linhas_transacionais"):
        partes.append(
            "Transacional:\n"
            + json.dumps(state["linhas_transacionais"], ensure_ascii=False)
        )
    if not partes:
        return "Sem consulta de catálogo nem de pedido."
    partes.append(
        "Se existir qt_disponivel, a disponibilidade é esse número, "
        "mesmo que o catálogo fale em últimas unidades."
    )
    return "\n\n".join(partes)


def criar_grafo(
    classificar: Callable[[str], str],
    redigir: Callable[[str, str], str],
    checkpointer,
    buscar=buscar_catalogo,
):
    def rotear(state: Estado) -> dict:
        mensagem = _ultima_mensagem(state)
        intencao: Intencao = "conversa"
        for tentativa in range(2):
            complemento = "" if tentativa == 0 else "\nResponda apenas o JSON."
            try:
                intencao = interpretar_intencao(classificar(mensagem + complemento))
                break
            except (ValidationError, ValueError, json.JSONDecodeError):
                continue
        return {
            "intencao": intencao,
            "trechos_catalogo": [],
            "linhas_transacionais": [],
        }

    def no_catalogo(state: Estado) -> dict:
        return {"trechos_catalogo": buscar(_ultima_mensagem(state))}

    def no_transacional(state: Estado) -> dict:
        mensagem = _ultima_mensagem(state)
        foco = state.get("id_pedido_em_foco")
        escolha = escolher_consulta(mensagem, foco)
        id_revendedora = state["id_revendedora"]
        if escolha == "margem":
            linha = consultar_minha_margem(id_revendedora=id_revendedora)
            linhas = [linha] if linha else []
        elif escolha == "estoque":
            linhas = consultar_estoque(produto_citado(mensagem) or mensagem)
        elif escolha == "pedido_em_foco":
            linhas = consultar_pedidos(id_revendedora=id_revendedora, id_pedido=foco)
        else:
            linhas = consultar_pedidos(id_revendedora=id_revendedora)
            if linhas:
                foco = linhas[0]["id_pedido"]
        return {"linhas_transacionais": linhas, "id_pedido_em_foco": foco}

    def no_redigir(state: Estado) -> dict:
        mensagem = _ultima_mensagem(state)
        resposta = redigir(mensagem, _montar_contexto(state))
        return {"resposta": resposta, "messages": [AIMessage(content=resposta)]}

    def no_recusar(state: Estado) -> dict:
        return {"resposta": RECUSA, "messages": [AIMessage(content=RECUSA)]}

    def depois_do_roteador(state: Estado) -> str:
        return {
            "catalogo": "buscar_catalogo",
            "pedido": "consultar_transacional",
            "ambos": "buscar_catalogo",
            "conversa": "redigir",
            "bloqueado": "recusar",
        }[state["intencao"]]

    def depois_do_catalogo(state: Estado) -> str:
        if state["intencao"] == "ambos":
            return "consultar_transacional"
        return "redigir"

    grafo = StateGraph(Estado)
    grafo.add_node("rotear", rotear)
    grafo.add_node("buscar_catalogo", no_catalogo)
    grafo.add_node("consultar_transacional", no_transacional)
    grafo.add_node("redigir", no_redigir)
    grafo.add_node("recusar", no_recusar)
    grafo.add_edge(START, "rotear")
    grafo.add_conditional_edges("rotear", depois_do_roteador)
    grafo.add_conditional_edges("buscar_catalogo", depois_do_catalogo)
    grafo.add_edge("consultar_transacional", "redigir")
    grafo.add_edge("redigir", END)
    grafo.add_edge("recusar", END)
    return grafo.compile(checkpointer=checkpointer)


def classificar_ollama(mensagem: str) -> str:
    from langchain_ollama import ChatOllama

    modelo = ChatOllama(model=LLM_MODEL, base_url=OLLAMA_BASE_URL, temperature=0)
    resposta = modelo.invoke(
        [
            (
                "system",
                "Classifique a mensagem da revendedora. "
                "Responda só um JSON: "
                '{"intencao":"catalogo"|"pedido"|"ambos"|"conversa"|"bloqueado"}. '
                "catalogo: promoção, preço de tabela, descrição. "
                "pedido: status, transportadora, estoque, margem própria, 'meu último pedido', 'dele'. "
                "ambos: promoção e estoque na mesma frase. "
                "bloqueado: margem ou dado pessoal de outra pessoa. "
                "conversa: saudação ou assunto fora disso.",
            ),
            ("human", mensagem),
        ]
    )
    conteudo = resposta.content
    return conteudo if isinstance(conteudo, str) else str(conteudo)


def redigir_ollama(mensagem: str, contexto: str) -> str:
    from langchain_ollama import ChatOllama

    modelo = ChatOllama(model=LLM_MODEL, base_url=OLLAMA_BASE_URL, temperature=0)
    resposta = modelo.invoke(
        [
            (
                "system",
                "Você é o assistente da revendedora. Responda em português, em uma ou duas frases, "
                "só com os dados recebidos. Se houver qt_disponivel, a disponibilidade é esse número.",
            ),
            ("human", f"Pergunta: {mensagem}\n\nDados:\n{contexto}"),
        ]
    )
    conteudo = resposta.content
    return conteudo if isinstance(conteudo, str) else str(conteudo)


def invocar(grafo, *, id_revendedora: int, id_sessao: str, mensagem: str) -> dict:
    config = {"configurable": {"thread_id": id_sessao}}
    grafo.invoke(
        {
            "messages": [HumanMessage(content=mensagem)],
            "id_revendedora": id_revendedora,
            "id_sessao": id_sessao,
        },
        config,
    )
    return grafo.get_state(config).values


@contextmanager
def abrir_grafo() -> Iterator:
    with PostgresSaver.from_conn_string(DATABASE_URL) as saver:
        saver.setup()
        yield criar_grafo(classificar_ollama, redigir_ollama, saver)
