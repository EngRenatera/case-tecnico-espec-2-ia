"""Ingestão e busca do catálogo.

A ingestão é um ETL de três passos: o PDF vira texto, o texto vira pedaços
e cada pedaço vira um vetor gravado em catalogo_chunk. A busca ordena esses
vetores pela distância e devolve os pedaços mais próximos da pergunta.
Disponibilidade não mora aqui.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

import psycopg
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
PDF_PATH = ROOT / "catalogo" / "ciclo-15.pdf"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
LOTE_EMBEDDING = 16

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://app:app@localhost:5433/agentes",
)
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "nomic-embed-text")


def quebrar(
    texto: str,
    tamanho: int = CHUNK_SIZE,
    sobreposicao: int = CHUNK_OVERLAP,
) -> list[str]:
    """Corta o texto em pedaços de até `tamanho` caracteres, com sobreposição.

    Quando há espaço, o corte cai no fim de uma palavra. Sem espaço, o corte
    é na posição exata, para o tamanho continuar previsível.
    """
    texto = " ".join(texto.split())
    if not texto:
        return []
    if sobreposicao < 0 or sobreposicao >= tamanho:
        raise ValueError("A sobreposição precisa ser menor que o tamanho do pedaço")
    if len(texto) <= tamanho:
        return [texto]

    pedacos: list[str] = []
    inicio = 0
    while inicio < len(texto):
        fim = min(inicio + tamanho, len(texto))
        if fim < len(texto):
            corte = texto.rfind(" ", inicio, fim)
            if corte > inicio:
                fim = corte
        pedaco = texto[inicio:fim].strip()
        if pedaco:
            pedacos.append(pedaco)
        if fim >= len(texto):
            break
        proximo = fim - sobreposicao
        if proximo <= inicio:
            proximo = fim
        if proximo < len(texto) and texto[proximo] != " ":
            espaco = texto.find(" ", proximo, fim)
            if espaco != -1:
                proximo = espaco + 1
        if proximo <= inicio:
            proximo = min(fim + 1, len(texto))
        inicio = proximo
    return pedacos


def extrair_paginas(pdf_path: Path) -> list[tuple[int, str]]:
    leitor = PdfReader(str(pdf_path))
    paginas: list[tuple[int, str]] = []
    for indice, pagina in enumerate(leitor.pages, start=1):
        texto = " ".join((pagina.extract_text() or "").split())
        if texto.strip():
            paginas.append((indice, texto))
    return paginas


def embed(textos: list[str]) -> list[list[float]]:
    if not textos:
        return []
    payload = json.dumps({"model": EMBEDDING_MODEL, "input": textos}).encode()
    pedido = urllib.request.Request(
        f"{OLLAMA_BASE_URL}/api/embed",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(pedido, timeout=120) as resposta:
            corpo = json.load(resposta)
    except urllib.error.URLError as erro:
        raise RuntimeError(
            f"Não foi possível chamar o embedding em {OLLAMA_BASE_URL}. O Ollama está no ar?"
        ) from erro

    vetores = corpo["embeddings"]
    if len(vetores) != len(textos):
        raise RuntimeError("O Ollama devolveu uma quantidade de vetores diferente dos pedaços")
    if len(vetores[0]) != 768:
        raise RuntimeError(
            f"O vetor veio com {len(vetores[0])} dimensões e a coluna embedding espera 768"
        )
    return vetores


def _vetor_sql(vetor: list[float]) -> str:
    return "[" + ",".join(f"{numero:.8f}" for numero in vetor) + "]"


def ingerir(pdf_path: Path = PDF_PATH) -> int:
    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF não encontrado em {pdf_path}. "
            "Gere com: uv run python scripts/gerar_catalogo_pdf.py"
        )

    registros: list[tuple[str, int]] = []
    for nr_pagina, texto in extrair_paginas(pdf_path):
        for pedaco in quebrar(texto):
            registros.append((pedaco, nr_pagina))
    if not registros:
        raise RuntimeError(f"{pdf_path.name} não tem texto para ingerir")

    vetores: list[list[float]] = []
    textos = [pedaco for pedaco, _ in registros]
    for inicio in range(0, len(textos), LOTE_EMBEDDING):
        vetores.extend(embed(textos[inicio : inicio + LOTE_EMBEDDING]))

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.transaction():
            conn.execute("TRUNCATE catalogo_chunk RESTART IDENTITY")
            for (pedaco, nr_pagina), vetor in zip(registros, vetores, strict=True):
                conn.execute(
                    """
                    INSERT INTO catalogo_chunk (des_conteudo, embedding, nm_arquivo, nr_pagina)
                    VALUES (%s, %s::vector, %s, %s)
                    """,
                    (pedaco, _vetor_sql(vetor), pdf_path.name, nr_pagina),
                )
    return len(registros)


def buscar_catalogo(pergunta: str, k: int = 4) -> list[str]:
    """Devolve os k pedaços do catálogo mais próximos da pergunta."""
    vetor = embed([pergunta])[0]
    with psycopg.connect(DATABASE_URL) as conn:
        linhas = conn.execute(
            """
            SELECT des_conteudo
            FROM catalogo_chunk
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (_vetor_sql(vetor), k),
        ).fetchall()
    return [linha[0] for linha in linhas]


def main(argv: list[str] | None = None) -> None:
    argumentos = list(sys.argv[1:] if argv is None else argv)
    if argumentos != ["ingerir"]:
        raise SystemExit("Uso: python -m app.rag ingerir")
    quantidade = ingerir()
    print(f"Ingeridos {quantidade} pedaços de {PDF_PATH.name}")


if __name__ == "__main__":
    main()
