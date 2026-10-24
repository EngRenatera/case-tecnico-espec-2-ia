# Ollama no MVP, Vertex AI só na evolução

Status: accepted

O MVP precisa rodar na máquina local, sem projeto GCP e sem créditos. Chat e embeddings ficam no Ollama: `qwen2.5:7b-instruct` e `nomic-embed-text`. A máquina de desenvolvimento tem 31 GB de RAM e só GPU integrada, então um modelo de 7B em 4 bits ainda responde em tempo de demonstração.

## Opções consideradas

- Vertex AI (Gemini): caminho natural da vaga, e exige projeto, credenciais e cota que quem for rodar o repositório pode não ter.
- API do Google AI Studio com chave: simples de configurar, e continua dependendo de rede e de cota fora do repositório.
- Ollama local: sobe no `docker compose`, sem conta. O grafo não muda quando o cliente do modelo for trocado por Vertex AI na narrativa de evolução.

## Consequências

- O README documenta o download dos modelos e o fallback `qwen2.5:3b-instruct` para máquinas com menos de 16 GB de RAM.
- A latência no CPU faz parte da demo. A seção de system design explica a troca pelo Gemini no Vertex AI sem reescrever o grafo.
