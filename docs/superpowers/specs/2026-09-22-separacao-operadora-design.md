# Separação de contatos por operadora — Design

**Data:** 2026-09-22

## Contexto e objetivo

O usuário tem uma planilha com 1.200 contatos de telefone e precisa classificar
cada um pela operadora de telefonia. Fazer isso manualmente não é viável;
o objetivo deste projeto é um script que automatiza essa classificação.

## Escopo

- Entrada: planilha Excel/CSV com uma coluna de números de celular brasileiros,
  já formatados com DDD (ex: `(65) 99946-9686` ou `65999469686`).
- Saída: a mesma planilha, com uma coluna nova `Operadora` preenchida.
- Método: identificação por **faixa de numeração** (DDD + prefixo do número),
  usando o Plano de Numeração público da Anatel.

## Fora de escopo (non-goals)

- Detectar a operadora **atual** de números portados. O método usado reflete a
  operadora **original** da faixa (a que a Anatel atribuiu o bloco), não o
  histórico de portabilidade. Essa limitação foi comunicada e aceita pelo
  usuário.
- Números fixos (o foco é celular).
- Interface gráfica — é um script rodado localmente.

## Fonte de dados e mecanismo de busca

A fonte é o Plano de Numeração da Anatel, disponibilizado por
[teleco.com.br/num_cel.asp](https://teleco.com.br/num_cel.asp) em uma tabela
por DDD (rodapé da página indica a data de referência, ex: "Fonte: Anatel.
Referente a Julho/26").

Investigação técnica confirmou um endpoint direto por trás do seletor de DDD
da página, que retorna a tabela em HTML:

```
POST https://teleco.com.br/carrega_numeros_operadora.asp?dd={DDD}
```

Retorna uma tabela HTML onde cada linha tem:
- Um `<img src=".../num_cel/{NomeOperadora}.png" ALT="{NomeOperadora}">` —
  o nome da operadora está no nome do arquivo de imagem (ex: `Vivo.png`,
  `TIM.png`, `Claro.png`, `Algar.png`).
- Uma ou mais faixas de prefixo (5 dígitos, ou intervalos `NNNNN-NNNNN`) logo
  em seguida.

O script busca essa tabela para os 67 DDDs válidos do Brasil — a mesma lista
fixa de códigos que aparece no seletor da própria página
(11 a 19, 21, 22, 24, 27, 28, 31 a 35, 37, 38, 41 a 49, 51, 53 a 55, 61 a 69,
71, 73 a 75, 77, 79, 81 a 89, 91 a 99) — e monta uma tabela local única:

```
ddd, operadora, prefixo_inicio, prefixo_fim
65, Vivo, 99600, 99665
65, Vivo, 99667, 99699
65, Vivo, 99800, 99850
65, Vivo, 99900, 99999
65, TIM, 98100, 98165
...
```

Essa busca roda **uma vez** (etapa de "montar tabela"), e o resultado fica
salvo em `tabela_operadoras.csv` no projeto. Rodar de novo (para atualizar com
dados mais recentes da Anatel) é uma ação manual/opcional, não acontece a cada
execução do classificador.

## Validação já feita

Testamos manualmente 3 números do DDD 65 contra a tabela buscada no endpoint
acima:

| Número | Prefixo (5 dígitos) | Faixa | Operadora |
|---|---|---|---|
| 65999469686 | 99946 | Vivo 99900-99999 | Vivo |
| 65996075347 | 99607 | Vivo 99600-99665 | Vivo |
| 65996728854 | 99672 | Vivo 99667-99699 | Vivo |

O usuário confirmou que o resultado está correto. Isso valida tanto a fonte de
dados quanto a lógica de comparação de faixas.

## Arquitetura

Script Python (3.14, já disponível na máquina), sem servidor nem banco de
dados, executado localmente via linha de comando.

### Componentes

1. **`montar_tabela.py`** — busca a tabela de faixas para todos os DDDs no
   endpoint da Teleco e salva em `tabela_operadoras.csv`. Roda uma vez (ou
   quando o usuário quiser atualizar os dados).
2. **`tabela_operadoras.csv`** — tabela local gerada pela etapa acima:
   `ddd, operadora, prefixo_inicio, prefixo_fim`.
3. **`normalizar_numero(numero)`** — limpa o número (remove espaços,
   parênteses, hífen, `+55`) e separa em `ddd` + `assinante` (8 ou 9 dígitos).
4. **`identificar_operadora(ddd, assinante)`** — pega os 5 primeiros dígitos
   do assinante (com o 9º dígito incluso) e procura na tabela local a faixa
   correspondente para aquele DDD. Retorna o nome da operadora ou
   `"Não identificado"`.
5. **`classificar_planilha.py`** — script principal: lê a planilha de entrada
   (pandas + openpyxl), aplica `normalizar_numero` + `identificar_operadora`
   em cada linha, adiciona a coluna `Operadora`, salva em um **novo** arquivo
   de saída (nunca sobrescreve o original).

### Fluxo de dados

```
tabela_operadoras.csv (gerada uma vez a partir da Anatel/Teleco)
                                    │
Excel de entrada (1.200 contatos)  │
        │                          │
        ▼                          ▼
   normalizar_numero  →  identificar_operadora
        │
        ▼
Excel de saída (contatos + coluna "Operadora")
```

## Tratamento de erros

- Número com menos de 10-11 dígitos após normalização → linha marcada
  `"Número inválido"` (não interrompe o processamento das demais).
- Prefixo não encontrado na tabela para aquele DDD → `"Não identificado"`
  (ex: número fixo, ou faixa não coberta pela tabela pública).
- Linhas vazias/nulas na coluna de telefone → ignoradas, com contagem exibida
  ao final da execução.
- Falha ao buscar dados da Teleco (rede fora do ar) na etapa de montagem da
  tabela → erro claro pedindo para tentar novamente, sem gerar tabela parcial
  silenciosamente.

## Teste

- Validação manual já realizada (seção acima) com 3 números reais confirmados
  pelo usuário.
- Antes de rodar nos 1.200 contatos, o script deve ser testado com uma amostra
  pequena adicional se o usuário quiser mais confiança.
