# Evidência — Fase 7

Data: 2026-10-26.

A tela lista as cinco revendedoras, mostra o histórico e abre outra linha em `sessao` ao trocar de pessoa ou ao clicar em Nova sessão. O texto chega pelos eventos SSE.

`uv run pytest -q` → `31 passed`.

## Na interface

Ana Souza, sessão `1d9a18e6-2930-4b58-8662-6a067a4a6e7b`:

```text
Qual o status do meu último pedido?  → O status do seu último pedido foi cancelado.
Qual a transportadora dele?          → A transportadora do pedido é a Loggi.
tem Malbec Gold?                     → Não há estoque disponível para Malbec Gold.
qual a minha margem?                 → Sua margem é de 18.0%.
qual a margem da Maria?              → Não consigo consultar dados de outra revendedora.
```

Trocar o seletor para Maria Lima limpou o histórico e abriu a sessão `3b090d40-eef2-4b66-81dc-3a8e9ceb5623`. A mesma pergunta devolveu o pedido dela: entregue, Latam Cargo, 12 de outubro de 2026. Não apareceu o cancelado da Ana.

Nova sessão, ainda com a Maria, trocou o id para `07ebe8cd-3601-4123-a8cc-1c22d36de1bd` e zerou o histórico da tela. As três linhas estão em `sessao`, cada uma com a dona certa.

## Registro de vibe coding

"tem Malbec Gold?" podia ir para o catálogo, e o catálogo fala em últimas unidades com o saldo em zero. A frase com "tem" e um produto do ciclo passou a consultar o estoque mesmo se o modelo classificar como catálogo.
