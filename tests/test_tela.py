"""A sessão nova nasce no Postgres. O SSE é só texto já fatiado."""

import json

import psycopg

from app.tela import criar_sessao, listar_revendedoras, texto_do_evento
from app.tools import DATABASE_URL


def test_nova_sessao_pertence_a_revendedora_escolhida():
    por_nome = {nome: id_revendedora for id_revendedora, nome in listar_revendedoras()}
    id_ana = por_nome["Ana Souza"]
    id_maria = por_nome["Maria Lima"]

    sessao_ana = criar_sessao(id_ana)
    sessao_maria = criar_sessao(id_maria)

    with psycopg.connect(DATABASE_URL) as conn:
        donos = dict(
            conn.execute(
                "SELECT id_sessao, id_revendedora FROM sessao WHERE id_sessao = ANY(%s)",
                ([sessao_ana, sessao_maria],),
            ).fetchall()
        )

    assert sessao_ana != sessao_maria
    assert donos[sessao_ana] == id_ana
    assert donos[sessao_maria] == id_maria


def test_evento_sse_devolve_o_pedaco_de_texto():
    linha = 'data: ' + json.dumps({"texto": "Olá "}, ensure_ascii=False)
    assert texto_do_evento(linha) == "Olá "
    assert texto_do_evento("") is None
    assert texto_do_evento("event: ping") is None
