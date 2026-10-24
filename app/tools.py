"""Consultas transacionais que o agente pode chamar.

O modelo só preenche o que está em ARGUMENTOS_DO_MODELO. O id da
revendedora entra pelo código da sessão. Estoque não recebe revendedora:
o saldo é do centro de distribuição.
"""

from __future__ import annotations

import os
from datetime import date
from decimal import Decimal

import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://app:app@localhost:5433/agentes",
)

ARGUMENTOS_DO_MODELO = {
    "consultar_pedidos": ["id_pedido"],
    "consultar_estoque": ["nome_produto"],
    "consultar_minha_margem": ["id_ciclo"],
}


def consultar_pedidos(*, id_revendedora: int, id_pedido: int | None = None) -> list[dict]:
    """Último pedido da revendedora, ou o pedido pedido se o id for dela."""
    sql = """
        WITH escolhido AS (
            SELECT id_pedido
            FROM pedido
            WHERE id_revendedora = %(id_revendedora)s
              AND (%(id_pedido)s::integer IS NULL OR id_pedido = %(id_pedido)s)
            ORDER BY dt_pedido DESC, id_pedido DESC
            LIMIT 1
        )
        SELECT
            p.id_pedido,
            p.dt_pedido,
            p.des_status,
            p.nm_transportadora,
            p.id_ciclo,
            COALESCE(
                json_agg(
                    json_build_object(
                        'nm_produto', pr.nm_produto,
                        'cd_sku', pr.cd_sku,
                        'qt_item', ip.qt_item,
                        'vl_preco', ip.vl_preco
                    )
                    ORDER BY pr.nm_produto
                ) FILTER (WHERE pr.id_produto IS NOT NULL),
                '[]'::json
            ) AS itens
        FROM pedido p
        JOIN escolhido e ON e.id_pedido = p.id_pedido
        LEFT JOIN item_pedido ip ON ip.id_pedido = p.id_pedido
        LEFT JOIN produto pr ON pr.id_produto = ip.id_produto
        GROUP BY p.id_pedido, p.dt_pedido, p.des_status, p.nm_transportadora, p.id_ciclo
    """
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        linha = conn.execute(
            sql,
            {"id_revendedora": id_revendedora, "id_pedido": id_pedido},
        ).fetchone()
    if linha is None:
        return []
    return [_linha_para_dict(linha)]


def consultar_estoque(nome_produto: str) -> list[dict]:
    """Saldo do centro de distribuição. O nome é comparado sem diferenciar maiúsculas."""
    nome = nome_produto.strip()
    if not nome:
        return []
    sql = """
        SELECT p.nm_produto, p.cd_sku, p.nm_marca, e.qt_disponivel
        FROM produto p
        JOIN estoque e USING (id_produto)
        WHERE p.nm_produto ILIKE %(nome)s
        ORDER BY p.nm_produto
    """
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        linhas = conn.execute(sql, {"nome": nome}).fetchall()
    return [_linha_para_dict(linha) for linha in linhas]


def consultar_minha_margem(*, id_revendedora: int, id_ciclo: int | None = None) -> dict | None:
    """Margem da revendedora da sessão. Sem ciclo, vale o ciclo vigente."""
    sql = """
        SELECT m.id_ciclo, c.nm_ciclo, m.vl_margem
        FROM margem m
        JOIN ciclo c ON c.id_ciclo = m.id_ciclo
        WHERE m.id_revendedora = %(id_revendedora)s
          AND (
                (%(id_ciclo)s::integer IS NOT NULL AND m.id_ciclo = %(id_ciclo)s)
             OR (%(id_ciclo)s::integer IS NULL AND c.fl_vigente)
          )
    """
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        linha = conn.execute(
            sql,
            {"id_revendedora": id_revendedora, "id_ciclo": id_ciclo},
        ).fetchone()
    if linha is None:
        return None
    return _linha_para_dict(linha)


def _linha_para_dict(linha: dict) -> dict:
    return {campo: _valor_simples(valor) for campo, valor in linha.items()}


def _valor_simples(valor):
    if isinstance(valor, date):
        return valor.isoformat()
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, list):
        return [_normalizar_item(item) for item in valor]
    return valor


def _normalizar_item(item):
    if isinstance(item, dict):
        return {chave: _valor_simples(valor) for chave, valor in item.items()}
    return _valor_simples(item)
