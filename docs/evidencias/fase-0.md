# Evidência — Fase 0

Data: 2026-10-24. Branch: `fase-0-banco`.

O container `agentes-postgres` (`pgvector/pgvector:pg16`) subiu pelo Docker Desktop. A porta no host é 5433. O Postgres que já estava na máquina segue em 5432.

## Consulta do último pedido da Ana

```text
 des_status | dt_pedido  | nm_transportadora
------------+------------+-------------------
 cancelado  | 2026-10-20 | Loggi
(1 row)
```

## Estoque do Malbec Gold

```text
 qt_disponivel
---------------
             0
(1 row)
```

## Teste repetível

`uv run pytest tests/test_fase_0.py -q` → `3 passed`.

O terceiro teste só confirma que a extensão `vector` está criada. A tabela `catalogo_chunk` existe e está vazia. A ingestão do PDF é a fase 2.

## Registro de vibe coding

O pedido desta fase foi executar o bloco "Fase 0" do `docs/PLANO.md`.

Ajustes feitos na mão, fora do texto gerado direto do plano:

- A publicação da porta foi para 5433. O plano pedia 5432, e essa porta já pertence ao Postgres local.
- O daemon usado foi o Docker Desktop. O socket do `dockerd` do sistema recusou o usuário atual.
- Maria, Joana, Carla e Rita ganharam um pedido cada. O plano detalhava só os quatro pedidos da Ana. Sem o pedido da Maria, a troca de revendedora na fase 7 não teria o que mostrar.
- `vl_margem` está em percentual (Ana 18, Maria 42, Carla 31).
- Há um índice único parcial para existir um único ciclo vigente.
