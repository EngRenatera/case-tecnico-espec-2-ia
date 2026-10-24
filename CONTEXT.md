# Assistente da Revendedora

Contexto do canal de venda direta: uma revendedora consulta, numa conversa, o catálogo do ciclo e a situação dos próprios pedidos.

## Language

**Revendedora**:
Pessoa do canal de venda direta que usa o assistente. A sessão já sabe quem ela é.
_Avoid_: vendedora, consultora, cliente, usuária

**Sessão**:
Conversa contínua pertencente a uma única revendedora. Uma revendedora pode ter várias sessões, e uma sessão não mistura outra revendedora.
_Avoid_: thread, chat, atendimento

**Ciclo**:
Período comercial do catálogo. O ciclo vigente deste contexto é o Ciclo 15. Quando a revendedora não informa o ciclo, vale o vigente.
_Avoid_: campanha, mês, safra

**Catálogo**:
Material publicado do ciclo com produtos, regras de promoção e preço de tabela.
_Avoid_: vitrine, base de produtos

**Produto**:
Item vendável oferecido no ciclo, com um código único e um nome usado pela revendedora.
_Avoid_: item, mercadoria

**Estoque**:
Quantidade disponível de um produto no centro de distribuição, igual para todas as revendedoras. É a referência de disponibilidade quando o catálogo diz outra coisa.
_Avoid_: saldo da revendedora, estoque consignado

**Pedido**:
Compra de uma revendedora, com data, status e transportadora. O último pedido é o de data mais recente, mesmo que esteja cancelado.
_Avoid_: compra, order

**Status do pedido**:
Situação de um pedido: faturado, em trânsito, entregue ou cancelado.
_Avoid_: situação, etapa

**Margem**:
Lucratividade da revendedora em um ciclo. Somente a própria revendedora pode conhecê-la.
_Avoid_: comissão, lucro, rentabilidade

**Preço de tabela**:
Preço anunciado no catálogo do ciclo.
_Avoid_: preço cheio, preço de vitrine

**Preço do pedido**:
Valor registrado na compra. É a referência quando a pergunta é sobre quanto a revendedora pagou.
_Avoid_: preço praticado, preço líquido
