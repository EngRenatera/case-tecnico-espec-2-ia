# Evidência — Fase 1

Data: 2026-10-24. Branch de trabalho: `fase-1-ollama`.

O container `agentes-ollama` (Ollama 0.40.10) escuta em `localhost:11434`. Os modelos ficam no volume `agentes_ollama`.

## Modelos

```text
NAME                       ID              SIZE      MODIFIED
qwen2.5:7b-instruct        845dbda0ea48    4.7 GB
nomic-embed-text:latest    0a109f422b47    274 MB
```

`LLM_MODEL` continua `qwen2.5:7b-instruct`. Uma frase curta levou 14,3 s na primeira chamada (o modelo ainda não estava na memória) e 3,2 s na segunda. As duas ficam abaixo dos 30 s do plano, então o fallback de 3B não entrou.

## Chat em streaming

`POST /api/chat` com `stream: true` devolveu 11 linhas JSON. O texto montado foi `Oi! Como posso ajudar você hoje?`. O modelo não obedeceu o "responda só: oi". Para esta fase o critério é a forma da resposta: várias linhas, não um JSON único.

## Embedding

`POST /api/embed` com `nomic-embed-text` e a entrada `Malbec Gold` devolveu um vetor de 768 números em 0,8 s. É a dimensão da coluna `catalogo_chunk.embedding`.

## Registro de vibe coding

O primeiro `ollama pull` falhou com `x509: certificate signed by unknown authority`. A máquina passa pelo Netskope, e o container não usa o bundle que o host usa (`SSL_CERT_FILE=/etc/netskope/certs/netskope-cert-bundle.pem`).

Ajuste feito na mão: o compose versionado continua portátil. O arquivo `docker-compose.netskope.yml` monta o bundle e define `SSL_CERT_FILE` dentro do container. Nesta máquina ele foi copiado para `docker-compose.override.yml`, que o Compose aplica sozinho e o git ignora. O bundle em `.certs/` também fica fora do git.

O pull seguinte baixou os dois modelos a cerca de 10 MB/s.
