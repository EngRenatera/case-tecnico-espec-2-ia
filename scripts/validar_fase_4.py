"""Duas mensagens na mesma sessão, com o Ollama e o checkpoint no Postgres."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import psycopg

from app.graph import abrir_grafo, invocar
from app.tools import DATABASE_URL

SESSAO = "fase4-ana-demo"


def main() -> None:
    with psycopg.connect(DATABASE_URL) as conn:
        id_ana = conn.execute(
            "SELECT id_revendedora FROM revendedora WHERE nm_revendedora = 'Ana Souza'"
        ).fetchone()[0]

    with abrir_grafo() as grafo:
        primeira = invocar(
            grafo,
            id_revendedora=id_ana,
            id_sessao=SESSAO,
            mensagem="Qual o status do meu último pedido?",
        )
        print("1", primeira["intencao"], primeira["resposta"])
        print("foco", primeira.get("id_pedido_em_foco"))
        segunda = invocar(
            grafo,
            id_revendedora=id_ana,
            id_sessao=SESSAO,
            mensagem="Qual a transportadora dele?",
        )
        print("2", segunda["intencao"], segunda["resposta"])
        print("foco", segunda.get("id_pedido_em_foco"))


if __name__ == "__main__":
    main()
