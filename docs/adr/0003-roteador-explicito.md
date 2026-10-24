# Roteador explícito em vez de loop ReAct

Status: accepted

O agente escolhe entre catálogo, sistema transacional, os dois, conversa livre ou recusa. Um nó devolve essa intenção em JSON validado por Pydantic, e arestas fixas levam ao nó correspondente. No ramo transacional, o código chama as tools e injeta a revendedora da sessão. O modelo não escolhe o identificador.

## Opções consideradas

- Loop ReAct (`create_react_agent`): o modelo escolhe a tool e pode repetir o ciclo. Num modelo local de 7B essa sequência erra, e a demo ao vivo fica instável.
- Roteador explícito: uma classificação, um contrato de saída e um caminho previsível para mostrar no code review.

## Consequências

- Pergunta que mistura promoção e estoque usa a intenção `ambos`. Se o roteador errar, o sintoma aparece numa aresta só e o teste mocka o LLM.
- O estado da sessão guarda o pedido em foco. A pergunta seguinte sobre a transportadora lê esse identificador do estado, em vez de pedir ao modelo para lembrar o número.
