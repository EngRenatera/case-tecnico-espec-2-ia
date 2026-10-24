"""Evidência repetível da fase 0. As duas consultas são as do plano."""

import os
from datetime import date

import psycopg

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://app:app@localhost:5433/agentes",
)


def test_ultimo_pedido_da_ana_inclui_cancelado():
    with psycopg.connect(DATABASE_URL) as conn:
        row = conn.execute(
            """
            SELECT des_status, dt_pedido, nm_transportadora
            FROM pedido
            WHERE id_revendedora = (
                SELECT id_revendedora
                FROM revendedora
                WHERE nm_revendedora = 'Ana Souza'
            )
            ORDER BY dt_pedido DESC
            LIMIT 1
            """
        ).fetchone()

    assert row == ("cancelado", date(2026, 10, 20), "Loggi")


def test_estoque_malbec_gold_esta_zerado():
    with psycopg.connect(DATABASE_URL) as conn:
        qt_disponivel = conn.execute(
            """
            SELECT qt_disponivel
            FROM estoque e
            JOIN produto p USING (id_produto)
            WHERE p.nm_produto = 'Malbec Gold'
            """
        ).fetchone()[0]

    assert qt_disponivel == 0


def test_pgvector_esta_habilitado():
    with psycopg.connect(DATABASE_URL) as conn:
        extname = conn.execute(
            "SELECT extname FROM pg_extension WHERE extname = 'vector'"
        ).fetchone()[0]

    assert extname == "vector"
