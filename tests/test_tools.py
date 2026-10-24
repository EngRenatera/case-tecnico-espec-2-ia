"""As tools leem o Postgres. Nenhum teste chama o modelo."""

import inspect

import psycopg
import pytest

from app.rag import DATABASE_URL
from app.tools import (
    ARGUMENTOS_DO_MODELO,
    consultar_estoque,
    consultar_minha_margem,
    consultar_pedidos,
)


def _id_revendedora(nome: str) -> int:
    with psycopg.connect(DATABASE_URL) as conn:
        return conn.execute(
            "SELECT id_revendedora FROM revendedora WHERE nm_revendedora = %s",
            (nome,),
        ).fetchone()[0]


def test_ultimo_pedido_da_ana_e_o_cancelado():
    pedidos = consultar_pedidos(id_revendedora=_id_revendedora("Ana Souza"))

    assert len(pedidos) == 1
    pedido = pedidos[0]
    assert pedido["des_status"] == "cancelado"
    assert pedido["dt_pedido"] == "2026-10-20"
    assert pedido["nm_transportadora"] == "Loggi"
    assert pedido["itens"][0]["nm_produto"] == "Malbec Gold"
    assert "nr_cpf" not in pedido


def test_pedido_da_ana_nao_aparece_para_a_maria():
    ana = _id_revendedora("Ana Souza")
    maria = _id_revendedora("Maria Lima")
    id_pedido = consultar_pedidos(id_revendedora=ana)[0]["id_pedido"]

    assert consultar_pedidos(id_revendedora=maria, id_pedido=id_pedido) == []


def test_estoque_do_malbec_gold_e_zero_para_qualquer_revendedora():
    assert "id_revendedora" not in inspect.signature(consultar_estoque).parameters

    linhas = consultar_estoque("Malbec Gold")

    assert linhas == [
        {
            "nm_produto": "Malbec Gold",
            "cd_sku": "BOT-001",
            "nm_marca": "Boticário",
            "qt_disponivel": 0,
        }
    ]
    assert consultar_estoque("malbec gold") == linhas


def test_margem_da_ana_no_ciclo_vigente_e_18():
    margem = consultar_minha_margem(id_revendedora=_id_revendedora("Ana Souza"))

    assert margem["id_ciclo"] == 15
    assert margem["nm_ciclo"] == "Ciclo 15"
    assert margem["vl_margem"] == 18


def test_margem_nao_aceita_revendedora_vinda_do_modelo():
    assert ARGUMENTOS_DO_MODELO["consultar_minha_margem"] == ["id_ciclo"]
    assert "id_revendedora" not in ARGUMENTOS_DO_MODELO["consultar_pedidos"]

    with pytest.raises(TypeError):
        consultar_minha_margem(id_ciclo=15)
