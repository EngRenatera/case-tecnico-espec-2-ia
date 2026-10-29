# Trace de cada mensagem no Langfuse

Status: accepted

Cada `POST /chat` pode virar um trace. A sessão do checkpoint vira a session do Langfuse, e o `id_revendedora` vira o user. As chaves `LANGFUSE_PUBLIC_KEY` e `LANGFUSE_SECRET_KEY` ligam o envio. Sem elas, o grafo responde e não abre cliente.

## Opções consideradas

- Phoenix ou Datadog: o case citava os três. Langfuse nomeia a execução do grafo do jeito que o LangGraph já é (um trace por mensagem, um span por nó) e o tier gratuito na nuvem dispensa subir ClickHouse.
- Self-host no compose: a stack atual pede ClickHouse, Redis e object storage, além de um Postgres separado. Isso compete com a demo e não explica o roteador.
- Só o callback do LangChain: cobre as duas chamadas ao Ollama e os nós, e deixa de fora a intenção crua, a ferramenta escolhida, a busca do catálogo e se a máscara alterou a frase.

## Consequências

- O callback entra em `invocar`. Spans manuais registram o roteamento, a ferramenta, a quantidade de trechos e o flag da máscara. O vetor do embedding fica de fora. A ingestão do PDF não gera trace.
- CPF, e-mail e telefone passam pela mesma máscara da saída antes da exportação. O texto do redator, anterior a essa máscara no grafo, sai no trace já limpo por essa função.
- O usuário do trace é o `id_revendedora`. Margem e pedido da sessão entram, porque são o contexto que o redator recebeu. No case o dado é sintético.
- O pytest tira as chaves do ambiente. Uma falha do Langfuse não derruba a resposta. O compose não sobe o serviço.
- O funil analítico da evolução continua no BigQuery, via Datastream. O Langfuse observa o caminho da resposta.
