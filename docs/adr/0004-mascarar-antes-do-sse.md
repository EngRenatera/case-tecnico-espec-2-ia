# Mascarar a resposta inteira antes de emitir o SSE

Status: accepted

O endpoint precisa parecer streaming, e a resposta não pode exibir CPF, telefone ou e-mail. A resposta do modelo é acumulada, a máscara é aplicada no texto completo, e só então o texto limpo segue em eventos SSE.

## Opções consideradas

- Streaming token a token: menor espera até a primeira palavra, e também o modo em que um CPF no meio da frase já chegou na tela.
- Resposta única, sem SSE: implementação menor, e abre mão do streaming pedido no case.
- Acumular, mascarar e fatiar o texto já limpo: a primeira palavra espera a frase inteira. No CPU local essa espera já existe por causa do modelo. O cliente ainda recebe a resposta em partes.

## Consequências

- A máscara de saída é determinística e entra no `pytest`, sem Ollama.
- Token a token com segurança exigiria segurar os últimos caracteres até ter certeza de que não formam um CPF. Isso fica fora do MVP.
