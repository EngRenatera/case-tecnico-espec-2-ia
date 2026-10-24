"""O roteador é mockado. As arestas e as tools rodam de verdade."""

import uuid

import psycopg
import pytest
from langgraph.checkpoint.memory import MemorySaver

from app.graph import RECUSA, criar_grafo, escolher_consulta, interpretar_intencao
from app.tools import DATABASE_URL


def _id_ana() -> int:
    with psycopg.connect(DATABASE_URL) as conn:
        return conn.execute(
            "SELECT id_revendedora FROM revendedora WHERE nm_revendedora = 'Ana Souza'"
        ).fetchone()[0]


def _nos(intencao: str, mensagem: str, buscar=None) -> tuple[list[str], dict]:
    chamadas = {"redigir": 0}

    def classificar(texto: str) -> str:
        return f'{{"intencao": "{intencao}"}}'

    def redigir(mensagem_usuario: str, contexto: str) -> str:
        chamadas["redigir"] += 1
        chamadas["contexto"] = contexto
        return "resposta"

    grafo = criar_grafo(
        classificar,
        redigir,
        MemorySaver(),
        buscar=buscar or (lambda pergunta: ["trecho do catálogo"]),
    )
    eventos = grafo.stream(
        {
            "messages": [{"role": "user", "content": mensagem}],
            "id_revendedora": _id_ana(),
            "id_sessao": uuid.uuid4().hex,
        },
        config={"configurable": {"thread_id": uuid.uuid4().hex}},
        stream_mode="updates",
    )
    nos = [next(iter(evento)) for evento in eventos]
    return nos, chamadas


def test_json_invalido_e_recusado():
    with pytest.raises(Exception):
        interpretar_intencao('{"intencao": "voo"}')


def test_json_com_cerca_e_aceito():
    assert interpretar_intencao('```json\n{"intencao": "catalogo"}\n```') == "catalogo"


def test_aresta_de_catalogo_nao_consulta_pedido():
    nos, _ = _nos("catalogo", "quais produtos estão em promoção?")
    assert nos == ["filtrar", "rotear", "buscar_catalogo", "redigir", "mascarar"]


def test_aresta_de_pedido_consulta_o_ultimo():
    nos, chamadas = _nos("pedido", "qual o status do meu último pedido?")
    assert nos == ["filtrar", "rotear", "consultar_transacional", "redigir", "mascarar"]
    assert "cancelado" in chamadas["contexto"]
    assert "Loggi" in chamadas["contexto"]


def test_aresta_ambos_passa_pelo_catalogo_e_pelo_transacional():
    nos, chamadas = _nos("ambos", "Malbec Gold está em promoção e tem estoque?")
    assert nos == ["filtrar", "rotear", "buscar_catalogo", "consultar_transacional", "redigir", "mascarar"]
    assert "qt_disponivel" in chamadas["contexto"]


def test_aresta_bloqueada_nao_redige():
    nos, chamadas = _nos("bloqueado", "oi, tudo bem?")
    assert nos == ["filtrar", "rotear", "recusar", "mascarar"]
    assert chamadas["redigir"] == 0


def test_segunda_mensagem_usa_o_pedido_em_foco():
    sessao = uuid.uuid4().hex
    foco = {}

    def classificar(texto: str) -> str:
        return '{"intencao": "pedido"}'

    def redigir(mensagem: str, contexto: str) -> str:
        return contexto

    grafo = criar_grafo(classificar, redigir, MemorySaver(), buscar=lambda pergunta: [])
    config = {"configurable": {"thread_id": sessao}}
    entrada = {"id_revendedora": _id_ana(), "id_sessao": sessao}

    grafo.invoke(
        {**entrada, "messages": [{"role": "user", "content": "qual o status do meu último pedido?"}]},
        config,
    )
    foco["id"] = grafo.get_state(config).values["id_pedido_em_foco"]
    grafo.invoke(
        {**entrada, "messages": [{"role": "user", "content": "qual a transportadora dele?"}]},
        config,
    )
    estado = grafo.get_state(config).values

    assert foco["id"] == estado["id_pedido_em_foco"]
    assert estado["linhas_transacionais"][0]["nm_transportadora"] == "Loggi"
    assert "Loggi" in estado["resposta"]


def test_escolher_consulta_prioriza_o_pedido_em_foco():
    assert escolher_consulta("qual a transportadora dele?", 10) == "pedido_em_foco"
    assert escolher_consulta("qual o status do meu último pedido?", None) == "ultimo_pedido"
    assert escolher_consulta("Malbec Gold está disponível?", 10) == "estoque"
    assert RECUSA.startswith("Não consigo")
