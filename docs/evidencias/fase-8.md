# Evidência — Fase 8

Data: 2026-10-26.

O README descreve como subir o MVP. O roteiro está em `docs/roteiro-demo.md`. A seção Evolução do README é a narrativa do slide e não tem deploy.

`uv run pytest -q` → `33 passed`.

## Oito falas na sessão da Ana

As falas 5 a 8 saíram na primeira passagem. As falas 1 a 4 foram repetidas depois de dois ajustes no roteador e no redator.

```text
1  A Instance está em promoção com 15% de desconto sobre o preço de tabela de R$ 149,90.
   O Rouge não tem promoção no Ciclo 15.
2  O Malbec Gold não está disponível, pois a quantidade disponível é 0.
3  O Malbec Gold está em promoção de últimas unidades, mas não tem estoque (qt_disponivel = 0).
4  Seu último pedido foi cancelado no dia 20 de outubro de 2026.
5  A transportadora do pedido é a Loggi.
6  Sua margem no ciclo 15 é de 18.0.
7  Não consigo consultar dados de outra revendedora.
8  Não consigo consultar dados de outra revendedora.
```

A fala 2, na primeira passagem, tinha sido classificada como conversa e o modelo respondeu que não havia informação de disponibilidade. A regra passou a mandar pergunta de produto e disponibilidade para o estoque.

A fala 1 cita a Instance, que é o trecho recuperado com preço de tabela. As regras do Malbec Gold e da Floratta também estão no contexto, e o 7B não as repetiu. O roteiro confere o preço que a busca de fato entrega.

## Registro de vibe coding

O relatório no README saiu dos registros em `docs/evidencias/`. O maior erro anotado continua sendo o 7B tratar "qual a minha margem?" como bloqueio. Nesta fase, o erro novo foi a disponibilidade cair em conversa.
