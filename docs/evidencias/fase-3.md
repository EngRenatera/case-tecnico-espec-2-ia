# Evidência — Fase 3

Data: 2026-10-24.

As três funções leem o Postgres. Nenhum teste chama o Ollama.

`uv run pytest tests/test_tools.py tests/test_fase_0.py tests/test_fase_2.py -q` → `11 passed`.

## O que a tool devolveu

Último pedido da Ana Souza:

```text
des_status: cancelado
dt_pedido: 2026-10-20
nm_transportadora: Loggi
item: Malbec Gold, qt_item 1, vl_preco 189.9
```

O mesmo `id_pedido`, pedido pela Maria, voltou `[]`.

Estoque de "Malbec Gold" e de "malbec gold": `qt_disponivel` 0. A função não tem parâmetro de revendedora.

Margem da Ana sem ciclo informado: ciclo 15, `vl_margem` 18.0. Chamar `consultar_minha_margem(id_ciclo=15)` sem o id da sessão levanta `TypeError`.

## Registro de vibe coding

O contrato que o modelo poderá preencher ficou explícito em `ARGUMENTOS_DO_MODELO`. `id_revendedora` não está nessa lista. Ele é argumento só por nome, preenchido pela sessão.

A data de criação do PDF passou a ser fixa. Sem isso, gerar o catálogo de novo mudava o binário mesmo com o mesmo texto, e o git acusava alteração.
