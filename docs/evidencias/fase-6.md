# Evidência — Fase 6

Data: 2026-10-26.

O `POST /chat` confere a dona da sessão, espera a frase inteira, mascara e só então corta em eventos `data: {"texto": "..."}`.

`uv run pytest -q` → `28 passed`. O teste do 403 e o do SSE não chamam o Ollama.

## Curl

Ana Souza é `id_revendedora` 1. Maria Lima é 2. A primeira chamada abre a sessão `fase6-ana-demo`.

```text
data: {"texto": "Olá! "}
data: {"texto": "Como "}
...
data: {"texto": "produtos."}
```

A mesma sessão com o id da Maria:

```text
403
{"detail":"Sessão de outra revendedora."}
```

O 403 sai antes do grafo. O teste troca o invocador por uma função que falha se for chamada, e ela não é chamada.

Um CPF `123.456.789-09` devolvido pelo grafo não aparece em nenhum evento. A frase remontada é a versão com `[cpf]`.

## Registro de vibe coding

A sessão ainda não existia na tabela. A primeira mensagem da Ana gravou a linha. A da Maria encontrou outra dona e parou. Sem essa ordem, o checkpoint aceitaria a thread e a conversa da Ana vazaria.
