"""Fase 2: o pedaço do catálogo cabe no contrato, e a busca devolve a promoção."""

from app.catalogo_pdf import gerar
from app.rag import buscar_catalogo, extrair_paginas, ingerir, quebrar


def test_quebrar_cobre_o_texto_com_sobreposicao():
    texto = "a" * 1000
    pedacos = quebrar(texto, tamanho=800, sobreposicao=100)

    assert pedacos[0] == "a" * 800
    assert len(pedacos[1]) == 300
    assert pedacos[0][-100:] == pedacos[1][:100]


def test_pdf_traz_a_promocao_do_malbec_gold(tmp_path):
    destino = tmp_path / "ciclo-15.pdf"
    gerar(destino=destino)
    texto = "\n".join(pagina for _, pagina in extrair_paginas(destino))

    assert "Malbec Gold" in texto
    assert "últimas unidades" in texto
    assert "qt_disponivel" not in texto


def test_busca_encontra_a_promocao_do_malbec_gold():
    ingerir()
    trechos = buscar_catalogo("promoção Malbec Gold")

    assert "está em promoção de últimas unidades" in trechos[0]
    assert "Malbec Gold" in trechos[0]
    assert "qt_disponivel" not in "\n".join(trechos)
