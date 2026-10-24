# Evidência — Fase 4

Data: 2026-10-24.

O grafo classifica a intenção, chama a tool em código e grava o state no Postgres na chave da sessão.

`uv run pytest tests/test_graph.py tests/test_tools.py tests/test_fase_0.py tests/test_fase_2.py -q` → `19 passed`.

Os testes de aresta mockam o modelo. O teste de memória usa o Postgres de verdade e o `MemorySaver`. O Ollama entra só no script manual.

## Duas mensagens, mesma sessão

`uv run python scripts/validar_fase_4.py`, sessão `fase4-ana-demo`:

```text
1 pedido O status do seu último pedido foi cancelado.
foco 1
2 pedido A transportadora do pedido é a Loggi.
foco 1
```

A segunda chamada não recebeu `id_pedido_em_foco`. O valor veio do checkpoint.

No Postgres, o passo `4` da thread é o `input` da segunda mensagem e já chega com `id_pedido_em_foco = 1`:

```text
passo  origem  foco
2      loop    1      <- o nó transacional gravou o último pedido
4      input   1      <- a segunda pergunta começa com o foco preenchido
```

## Registro de vibe coding

O 7B classificou as duas frases como `pedido`. A escolha entre "último pedido" e "o pedido em foco" ficou numa função, `escolher_consulta`, porque "dele" e "transportadora" são regra, não um segundo loop do modelo.
