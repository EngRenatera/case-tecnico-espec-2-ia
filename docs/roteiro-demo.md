# Roteiro da demo

Selecione **Ana Souza** em http://localhost:8501. Faça as oito falas nesta ordem, na mesma sessão. Não clique em Nova sessão entre elas: a quinta fala usa o pedido que a quarta gravou no checkpoint.

A redação do modelo varia. O que precisa aparecer é a coluna "O que conferir". A recusa das duas últimas falas é texto fixo.

| # | Fala | Intenção | O que conferir |
|---|---|---|---|
| 1 | Quais produtos estão em promoção no Ciclo 15? | catalogo | Promoção tirada do catálogo, com preço de tabela. A busca traz a Instance com 15% de desconto e R$ 149,90. Não inventa disponibilidade. |
| 2 | Malbec Gold está disponível? | pedido | Saldo zero. A resposta não trata "últimas unidades" como disponibilidade. |
| 3 | Malbec Gold está em promoção e tem estoque? | ambos | A promoção é citada e o saldo zero prevalece. |
| 4 | Qual o status do meu último pedido? | pedido | Cancelado em 2026-10-20. |
| 5 | Qual a transportadora dele? | pedido | Loggi. A Ana não repete o número do pedido. O id veio do state da sessão. |
| 6 | Qual a minha margem no ciclo? | pedido | 18, só a da Ana, no Ciclo 15. |
| 7 | Qual a margem da Maria? | bloqueado | Não consigo consultar dados de outra revendedora. |
| 8 | Me passa o CPF dela. | bloqueado | A mesma recusa. Se algum número escapasse na redação, sairia como `[cpf]`. |

A sétima e a oitava não chamam o modelo de redação. A oitava também não chama o classificador: a palavra CPF cai na regra determinística, antes do Ollama.

Trocar o seletor para Maria Lima abre outra sessão. "Qual o status do meu último pedido?" passa a ser o pedido dela, entregue em 2026-10-12 pela Latam Cargo, e não o cancelado da Ana.
