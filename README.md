# Assistente da revendedora

MVP local do case de Especialista II de Engenharia de IA. Uma revendedora pergunta, em português, sobre o catálogo do Ciclo 15, o próprio pedido, o estoque do centro de distribuição e a própria margem. O grafo recusa margem e dado pessoal de outra pessoa.

Tudo roda na máquina: Postgres com pgvector, Ollama, FastAPI e Streamlit. A nuvem fica na seção [Evolução](#evolução) e não está implementada.

## Pré-requisitos

- Docker com `docker compose`
- [uv](https://docs.astral.sh/uv/)
- Cerca de 16 GB de RAM para o modelo de 7B. Abaixo disso, ou se uma frase curta passar de cerca de 30 segundos, use o modelo de 3B descrito mais abaixo. A máquina usada no desenvolvimento tem 31 GB e só GPU integrada. O chat no CPU é o esperado.

## Subir

Na raiz do repositório:

```bash
docker compose up -d
docker compose exec ollama ollama pull qwen2.5:7b-instruct
docker compose exec ollama ollama pull nomic-embed-text
uv sync
uv run python -m app.rag ingerir
```

O Postgres publica a porta **5433** no host, porque a 5432 já costuma estar ocupada. Usuário, senha e base são `app` / `app` / `agentes`. Os padrões do código são os mesmos do `.env.example`. Copiar o arquivo só é necessário para mudar alguma variável.

O `ingerir` lê `catalogo/ciclo-15.pdf`, quebra o texto e grava os vetores de 768 dimensões. Sem esse passo, a pergunta de promoção não tem o que buscar.

Se o `ollama pull` falhar com `x509: certificate signed by unknown authority`, a rede está reescrevendo o certificado. O compose base continua portátil. Nesta rede, o ajuste é o overlay `docker-compose.netskope.yml`: copiar o bundle para `.certs/` e o overlay para `docker-compose.override.yml`. Os dois arquivos ficam fora do git. O comentário no topo do overlay tem os comandos.

### Fallback de 3B

O grafo não muda. Baixe o modelo menor e exporte a variável no mesmo terminal da API:

```bash
docker compose exec ollama ollama pull qwen2.5:3b-instruct
export LLM_MODEL=qwen2.5:3b-instruct
```

## Rodar a demo

Dois terminais, na raiz:

```bash
uv run uvicorn app.main:app --port 8000
```

```bash
uv run streamlit run app/tela.py
```

Abra http://localhost:8501. Selecione **Ana Souza** e siga [docs/roteiro-demo.md](docs/roteiro-demo.md) na mesma sessão, sem clicar em Nova sessão no meio das oito falas. A primeira palavra de cada resposta espera a frase inteira: a máscara corre no texto completo e só então o SSE corta em partes.

A API também responde em http://localhost:8000/docs, no `POST /chat`. O `id_revendedora` da Ana, nesta semente, é `1`. Uma sessão de outra revendedora na mesma thread responde 403 antes do grafo.

## Testes

O Postgres e o Ollama precisam estar no ar. O teste do catálogo chama o modelo de embedding.

```bash
uv run pytest -q
```

## Decisões

| Decisão | Registro |
|---|---|
| Ollama no MVP, Vertex só na narrativa | [docs/adr/0001-ollama-no-mvp.md](docs/adr/0001-ollama-no-mvp.md) |
| Vetores no mesmo Postgres dos pedidos | [docs/adr/0002-pgvector-no-mesmo-postgres.md](docs/adr/0002-pgvector-no-mesmo-postgres.md) |
| Roteador explícito, sem loop ReAct | [docs/adr/0003-roteador-explicito.md](docs/adr/0003-roteador-explicito.md) |
| Mascarar a frase inteira antes do SSE | [docs/adr/0004-mascarar-antes-do-sse.md](docs/adr/0004-mascarar-antes-do-sse.md) |

O glossário do domínio está em [CONTEXT.md](CONTEXT.md). O plano de construção está em [docs/PLANO.md](docs/PLANO.md).

## Evolução

Esta seção é o que se desenha no slide. Nada abaixo está no `docker compose`.

Quinhentas mil é a base de revendedoras cadastradas, não quinhentos mil sockets ao mesmo tempo. O tamanho do Cloud Run e do pool de conexões sai do pico concorrente, na ordem de milhares.

A API vai para o Cloud Run, com várias instâncias e sem afinidade de sessão. O state da conversa está no checkpoint, chaveado por `id_sessao`. Qualquer instância retoma a thread.

O banco operacional é Cloud SQL for PostgreSQL, com pgvector, e um pool (PgBouncer) porque cada instância do Cloud Run abre conexão. Pedido, estoque e margem continuam nesse Postgres. Se a tool virar gargalo, entra uma réplica de leitura.

A tool não consulta o BigQuery. Consulta analítica tem latência de segundos e cobra os bytes lidos. O chat precisa de uma linha por chave primária. O lake fica fora do caminho da resposta.

O Datastream faz CDC do Postgres, por replicação lógica, para um dataset bruto no BigQuery. A squad de dados lê pedidos, margens agregadas e o funil de intenções. O agente não lê esse dataset.

O modelo troca o cliente Ollama pelo cliente Vertex AI (Gemini). As intenções e o grafo permanecem. Os embeddings podem ir para o modelo de embedding do Vertex. A dimensão do vetor muda, e os chunks são reindexados.

A máscara por regex vira uma chamada ao Sensitive Data Protection, no mesmo ponto do grafo: depois da redação, antes do SSE.

Este ciclo cabe no pgvector. Um acervo de muitos ciclos e marcas pode ir para o Vertex AI Vector Search. A função `buscar_catalogo` troca a implementação. O grafo permanece.

## Observaçãoes para Testes

### Perguntas sugeridas para testes: 

| Perguntas |
|---|
| Qual o status do meu último pedido? |
| Qual a minha margem? |
| Qual a margem da Maria? |
| Qual o valor do último pedido? |
| Qual é a transportadora do meu último pedido? |

### Pontos que o agentes não faz
- Registrar novos pedidos
- Saudações
- Outros temas 
- Contexto longos*

*O modelo utilizado nesse MVP é bem mais limitado aos modelos famosos conhecidos. Para efeitos de referência o modelo utilizado processa até 30mil tokens, enquanto o Gemini pode passar de 1 milhão de tokens.


## Relatório de Vibe Coding

### Resumo da sessão

A sessão começou pelo PDF do case. O pedido foi planejar o MVP antes de escrever código: prazo, stack local, o que ficava só no slide e o que entrava no repositório. Desse plano saíram as fases 0 a 8, cada uma com um comando de validação e um registro em `docs/evidencias/`.

O que foi construído, nesta ordem: Postgres com a semente do Ciclo 15, Ollama, catálogo em PDF ingerido no pgvector, tools de pedido, estoque e margem, grafo com memória de sessão, guardrails, API com SSE, tela Streamlit e o README com o roteiro e a narrativa de evolução. No fim, o repositório foi tornado público e a fala de cerca de 40 minutos foi escrita em `apresentacao/`.

### Ferramentas

O código foi escrito no Cursor, com o agente da IDE. A validação de cada fase rodou no terminal: `uv`, `pytest`, Docker Compose, Postgres e Ollama. A tela foi conferida no navegador. Não houve Copilot, ChatGPT nem Claude nesta sessão.

### Como os prompts iniciais foram estruturados

O primeiro prompt colou o caminho do PDF e pediu um plano fase a fase, com uma forma de validar cada fase antes de seguir. As respostas fecharam as decisões em rodadas curtas: local em vez de GCP, Postgres na porta 5433, roteador explícito, observabilidade só depois do roteiro.

Com o plano gravado em `docs/PLANO.md`, cada prompt seguinte foi uma frase: executar a fase N. O bloco da fase já trazia o que aprender, o que fazer e o comando que prova. Quando o resultado divergia, o prompt seguinte descrevia o sintoma visto na tela, no teste ou no banco. Não pedia um genérico "melhore".

### Maior obstáculo e correção

Na primeira pergunta ao vivo, "qual a minha margem?", o 7B devolveu `bloqueado`. O prompt de classificação dizia que margem de outra pessoa era recusa, e o modelo generalizou para qualquer margem. A regra determinística já tinha deixado a frase passar. O classificador desfazia isso.

A correção foi em dois lugares. O prompt ganhou um exemplo separando "qual a minha margem?" de "qual a margem da Maria?". O código passou a ignorar um `bloqueado` do modelo quando a frase é a margem da sessão. A consulta continua presa ao id da revendedora autenticada. A resposta da Ana voltou a ser 18, no Ciclo 15.
