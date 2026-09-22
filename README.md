# Separação de contatos por operadora

Classifica uma planilha de contatos pela operadora de telefonia (Vivo, Claro,
TIM, Oi e outras), usando o Plano de Numeração público da Anatel.

**Importante:** identifica a operadora *original* da faixa do número, não a
atual — números portados para outra operadora não são detectados por este
método.

## Uso

1. Instale as dependências (uma vez):

   pip install -r requirements.txt

2. Gere a tabela de faixas (uma vez, ou quando quiser atualizar os dados):

   python montar_tabela.py

3. Classifique sua planilha:

   python classificar_planilha.py minha_planilha.xlsx NomeDaColunaComTelefone tabela_operadoras.csv resultado.xlsx

   O arquivo `resultado.xlsx` é uma cópia da sua planilha original com uma
   coluna nova chamada `Operadora`. O arquivo original não é alterado.

## Valores possíveis na coluna Operadora

- Nome da operadora (ex: `Vivo`, `TIM`, `Claro`) — quando o prefixo do número
  está mapeado na tabela.
- `Não identificado` — número de celular válido, mas o prefixo não está
  cadastrado na tabela (ou é um número fixo).
- `Número inválido` — o valor da célula não parece um telefone brasileiro
  válido.
- `Vazio` — a célula estava em branco.
