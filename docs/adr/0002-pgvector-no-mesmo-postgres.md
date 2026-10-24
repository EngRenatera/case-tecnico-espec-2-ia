# pgvector no mesmo Postgres dos pedidos

Status: accepted

O catálogo vira embeddings e a busca precisa responder dentro da conversa. Os vetores ficam na extensão pgvector do mesmo Postgres que guarda pedidos, estoque, margem e o checkpoint da sessão.

## Opções consideradas

- Vertex AI Vector Search: endpoint com custo fixo, desproporcional para um catálogo de cerca de 25 produtos.
- BigQuery Vector Search: o lake analítico não é caminho de chat. Latência e custo por consulta não cabem numa resposta de assistente.
- Chroma em memória: perde os vetores quando o processo reinicia e fica separado da sessão, que já está no Postgres.
- pgvector: a busca é uma ordenação por distância com `LIMIT`, no mesmo SQL do restante do domínio.

## Consequências

- A dimensão do vetor fica fixa em 768, a do `nomic-embed-text`. Trocar o modelo de embedding exige reindexar os chunks.
- No desenho de 500 mil revendedoras, este catálogo continua em pgvector. O que precisa escalar é a conexão com o banco e o LLM, não o índice do ciclo.
