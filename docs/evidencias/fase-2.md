# Evidência — Fase 2

Data: 2026-10-24.

O Markdown `catalogo/ciclo-15.md` é a fonte. O script gera `catalogo/ciclo-15.pdf`. A ingestão leu o PDF, não o Markdown, e gravou 29 pedaços em `catalogo_chunk`.

## Busca

`buscar_catalogo("promoção Malbec Gold")` devolveu, no primeiro pedaço:

```text
Malbec Gold SKU BOT-001. Marca Boticário. Preço de tabela: R$ 189,90. Promoção do Ciclo 15: Malbec Gold está em promoção de últimas unidades. É a edição especial da linha Malbec, no frasco dourado, com a mesma família olfativa amadeirada.
```

Não há `qt_disponivel` nesse texto. Disponibilidade continua na tabela `estoque`.

## Testes

`uv run pytest -q` → `6 passed`. Os três novos cobrem o corte dos pedaços, o texto extraído do PDF e a busca da promoção.

## Registro de vibe coding

O primeiro PDF quebrou no caractere de bullet: o fpdf2 recusou desenhar um glifo sem largura útil. Troquei por hífen e passei a reposicionar a margem antes de cada linha.

A janela fixa de 800 caracteres juntou, no mesmo pedaço, a promoção do Malbec Gold e a frase do Malbec comum que diz "não entra na promoção". A busca ranqueava essa negação primeiro. Cada produto passou a abrir uma página. O pedaço fica menor que 800 caracteres e a sobreposição de 100 só vale se um produto passar desse tamanho. O corte também procura o último espaço, para não partir uma palavra.

O script `scripts/gerar_catalogo_pdf.py` inclui a raiz do repositório no `sys.path` porque o projeto ainda não é instalado como pacote. `python -m app.rag` não precisa disso quando roda na raiz.
