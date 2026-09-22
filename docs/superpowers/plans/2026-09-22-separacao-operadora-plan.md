# Separação de contatos por operadora — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Script Python que classifica cada contato de uma planilha (até 1.200
linhas) com a operadora de telefonia original do número, usando o Plano de
Numeração público da Anatel.

**Architecture:** Três módulos independentes: (1) `montar_tabela.py` busca as
faixas de numeração por DDD no endpoint público da Teleco e grava uma tabela
local `tabela_operadoras.csv`; (2) `operadora.py` contém a lógica pura de
normalização de número e busca de operadora na tabela; (3)
`classificar_planilha.py` lê a planilha do usuário, aplica `operadora.py` e
grava uma nova planilha com a coluna `Operadora`.

**Tech Stack:** Python 3.14 (já instalado), `pandas` + `openpyxl` (leitura/
escrita de Excel), `pytest` (testes), `urllib.request` da biblioteca padrão
(HTTP, sem dependência extra).

**Spec:** [docs/superpowers/specs/2026-09-22-separacao-operadora-design.md](../specs/2026-09-22-separacao-operadora-design.md)

## Global Constraints

- Python 3.14, já instalado na máquina — não requer outra versão.
- Nunca sobrescrever o arquivo de entrada do usuário; a saída é sempre um
  arquivo novo.
- Fonte de dados: `POST https://teleco.com.br/carrega_numeros_operadora.asp?dd={DDD}`
  (endpoint confirmado por inspeção de rede durante o brainstorming).
- A coluna nova na planilha de saída deve se chamar exatamente `Operadora`.
- Strings de status usadas pelo pipeline (contrato entre módulos, usado nos
  testes): `"Não identificado"` e `"Número inválido"`.

---

## Task 1: Estrutura do projeto e dependências

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `tests/` (diretório)
- Create: `tests/fixtures/` (diretório)

**Interfaces:**
- Consumes: nada (primeira task)
- Produces: ambiente com `pandas`, `openpyxl` e `pytest` instalados e
  importáveis; estrutura de pastas para as próximas tasks.

- [ ] **Step 1: Criar `requirements.txt`**

```text
pandas
openpyxl
pytest
```

- [ ] **Step 2: Instalar as dependências**

Run: `pip install -r requirements.txt`
Expected: instalação concluída sem erros.

- [ ] **Step 3: Criar `.gitignore`**

```text
__pycache__/
.pytest_cache/
tabela_operadoras.csv
```

- [ ] **Step 4: Criar os diretórios de teste**

Run: `mkdir -p tests/fixtures`
Expected: diretórios `tests/` e `tests/fixtures/` existem.

- [ ] **Step 5: Verificar que o pytest roda**

Run: `pytest --version`
Expected: imprime a versão do pytest instalado, sem erro.

- [ ] **Step 6: Commit**

```bash
git init
git add requirements.txt .gitignore
git commit -m "chore: estrutura inicial do projeto"
```

---

## Task 2: Módulo `operadora.py` — normalização e busca de faixa

**Files:**
- Create: `operadora.py`
- Test: `tests/test_operadora.py`

**Interfaces:**
- Consumes: nada (módulo puro, sem I/O externo além de ler um CSV local)
- Produces:
  - `carregar_tabela(caminho_csv: str) -> dict[str, list[tuple[int, int, str]]]`
  - `normalizar_numero(numero) -> tuple[str, str] | None`
  - `identificar_operadora(ddd: str, assinante: str, tabela: dict[str, list[tuple[int, int, str]]]) -> str`

  Essas três funções são usadas por `classificar_planilha.py` na Task 4.

- [ ] **Step 1: Escrever os testes (arquivo completo)**

Create `tests/test_operadora.py`:

```python
import csv
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from operadora import normalizar_numero, identificar_operadora, carregar_tabela


def _tabela_teste():
    return {
        "65": [
            (99600, 99665, "Vivo"),
            (99667, 99699, "Vivo"),
            (99800, 99850, "Vivo"),
            (99900, 99999, "Vivo"),
            (98100, 98165, "TIM"),
        ]
    }


def test_normalizar_numero_com_ddi():
    assert normalizar_numero("+55 65 99946-9686") == ("65", "999469686")


def test_normalizar_numero_sem_ddi():
    assert normalizar_numero("65999469686") == ("65", "999469686")


def test_normalizar_numero_formatado():
    assert normalizar_numero("(65) 99607-5347") == ("65", "996075347")


def test_normalizar_numero_ddd_igual_a_55_nao_e_confundido_com_ddi():
    assert normalizar_numero("55991234567") == ("55", "991234567")


def test_normalizar_numero_invalido_curto():
    assert normalizar_numero("12345") is None


def test_normalizar_numero_invalido_texto():
    assert normalizar_numero("não é telefone") is None


def test_identificar_operadora_vivo_prefixo_inicio_faixa():
    tabela = _tabela_teste()
    assert identificar_operadora("65", "999469686", tabela) == "Vivo"


def test_identificar_operadora_vivo_outro_numero():
    tabela = _tabela_teste()
    assert identificar_operadora("65", "996075347", tabela) == "Vivo"
    assert identificar_operadora("65", "996728854", tabela) == "Vivo"


def test_identificar_operadora_tim():
    tabela = _tabela_teste()
    assert identificar_operadora("65", "981234567", tabela) == "TIM"


def test_identificar_operadora_ddd_sem_faixas_cadastradas():
    tabela = _tabela_teste()
    assert identificar_operadora("11", "999469686", tabela) == "Não identificado"


def test_identificar_operadora_prefixo_fora_de_qualquer_faixa():
    tabela = _tabela_teste()
    assert identificar_operadora("65", "970000000", tabela) == "Não identificado"


def test_identificar_operadora_assinante_com_8_digitos_nao_identificado():
    tabela = _tabela_teste()
    assert identificar_operadora("65", "99469686", tabela) == "Não identificado"


def test_carregar_tabela(tmp_path):
    caminho = tmp_path / "tabela.csv"
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(["ddd", "operadora", "prefixo_inicio", "prefixo_fim"])
        escritor.writerow(["65", "Vivo", "99600", "99665"])
        escritor.writerow(["65", "TIM", "98100", "98165"])
    tabela = carregar_tabela(str(caminho))
    assert tabela == {
        "65": [(99600, 99665, "Vivo"), (98100, 98165, "TIM")]
    }
```

- [ ] **Step 2: Rodar os testes e confirmar que falham**

Run: `pytest tests/test_operadora.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'operadora'` (o arquivo
ainda não existe).

- [ ] **Step 3: Implementar `operadora.py`**

Create `operadora.py`:

```python
"""Lógica pura de normalização de número e identificação de operadora."""

import csv
import re


def carregar_tabela(caminho_csv: str) -> dict[str, list[tuple[int, int, str]]]:
    """Carrega tabela_operadoras.csv e retorna dict ddd -> [(inicio, fim, operadora)]."""
    tabela: dict[str, list[tuple[int, int, str]]] = {}
    with open(caminho_csv, newline="", encoding="utf-8") as f:
        leitor = csv.DictReader(f)
        for linha in leitor:
            ddd = linha["ddd"]
            inicio = int(linha["prefixo_inicio"])
            fim = int(linha["prefixo_fim"])
            operadora = linha["operadora"]
            tabela.setdefault(ddd, []).append((inicio, fim, operadora))
    return tabela


def normalizar_numero(numero) -> tuple[str, str] | None:
    """Extrai (ddd, assinante) de um número em qualquer formato comum.

    Retorna None se não for possível reconhecer um número de telefone
    brasileiro válido (DDD de 2 dígitos + assinante de 8 ou 9 dígitos).
    """
    apenas_digitos = re.sub(r"\D", "", str(numero))
    if apenas_digitos.startswith("55") and len(apenas_digitos) in (12, 13):
        apenas_digitos = apenas_digitos[2:]
    if len(apenas_digitos) not in (10, 11):
        return None
    ddd = apenas_digitos[:2]
    assinante = apenas_digitos[2:]
    return ddd, assinante


def identificar_operadora(
    ddd: str, assinante: str, tabela: dict[str, list[tuple[int, int, str]]]
) -> str:
    """Identifica a operadora original da faixa de um número de celular.

    Só identifica números móveis completos (assinante com 9 dígitos,
    incluindo o nono dígito). Qualquer outro caso retorna "Não identificado".
    """
    if len(assinante) != 9:
        return "Não identificado"
    prefixo = int(assinante[:5])
    for inicio, fim, operadora in tabela.get(ddd, []):
        if inicio <= prefixo <= fim:
            return operadora
    return "Não identificado"
```

- [ ] **Step 4: Rodar os testes e confirmar que passam**

Run: `pytest tests/test_operadora.py -v`
Expected: PASS em todos os testes.

- [ ] **Step 5: Commit**

```bash
git add operadora.py tests/test_operadora.py
git commit -m "feat: normalização de número e busca de operadora por faixa"
```

---

## Task 3: Módulo `montar_tabela.py` — busca das faixas na Teleco/Anatel

**Files:**
- Create: `montar_tabela.py`
- Create: `tests/fixtures/ddd65.html`
- Test: `tests/test_montar_tabela.py`

**Interfaces:**
- Consumes: nada de outra task (módulo independente)
- Produces:
  - `DDDS: list[int]` — lista fixa dos 67 DDDs válidos do Brasil
  - `buscar_html_ddd(ddd: int) -> str`
  - `parsear_faixas(html_bruto: str) -> list[tuple[str, int, int]]`
  - `escrever_csv(linhas: list[tuple[str, str, int, int]], caminho_saida: str) -> None`
  - `gerar_tabela(caminho_saida: str = "tabela_operadoras.csv") -> None`

  `gerar_tabela` é o que a Task 5 roda para produzir o
  `tabela_operadoras.csv` que `operadora.carregar_tabela` (Task 2) espera.

- [ ] **Step 1: Criar o fixture com a resposta real do endpoint (DDD 65)**

Create `tests/fixtures/ddd65.html` com este conteúdo exato (capturado do
endpoint `POST https://teleco.com.br/carrega_numeros_operadora.asp?dd=65`
durante o brainstorming, referente a Julho/2026):

```html
<table width="100%"  border="0" cellpadding="5" cellspacing="0">
<tr>
	<td width="90" class="textobasebold" style="border-bottom:#003 dotted 1px;" >Operadora</th>
	<td class="textobasebold" style="border-bottom:#003 dotted 1px;" >Faixa</th>	
</tr>

    <tr>
    <td style="border-bottom:#003 dotted 1px;" >
    
    <img src="http://www.teleco.com.br/imagens/logos/num_cel/Algar.png" style="width:72px; height:72px;" ALT="Algar"  />
    </td>
    <td style="border-bottom:#003 dotted 1px;" >
96000 &nbsp;


    <tr>
    <td style="border-bottom:#003 dotted 1px;" >
	
    <img src="http://www.teleco.com.br/imagens/logos/num_cel/America Net.png" style="width:72px; height:72px;"  />
    </td>
    <td style="border-bottom:#003 dotted 1px;" >
93500- &nbsp;


    <tr>
    <td style="border-bottom:#003 dotted 1px;" >
	
    <img src="http://www.teleco.com.br/imagens/logos/num_cel/Arqia.png" style="width:72px; height:72px;"  />
    </td>
    <td style="border-bottom:#003 dotted 1px;" >
97601-97604 &nbsp;


    <tr>
    <td style="border-bottom:#003 dotted 1px;" >
	
    <img src="http://www.teleco.com.br/imagens/logos/num_cel/Brisanet.png" style="width:72px; height:72px;"  />
    </td>
    <td style="border-bottom:#003 dotted 1px;" >
92140 &nbsp;


    <tr>
    <td style="border-bottom:#003 dotted 1px;" >
	
    <img src="http://www.teleco.com.br/imagens/logos/num_cel/Claro.png" style="width:72px; height:72px;"  />
    </td>
    <td style="border-bottom:#003 dotted 1px;" >
97400 &nbsp;

99200-99363 &nbsp;


    <tr>
    <td style="border-bottom:#003 dotted 1px;" >
	
    <img src="http://www.teleco.com.br/imagens/logos/num_cel/Surf.png" style="width:72px; height:72px;"  />
    </td>
    <td style="border-bottom:#003 dotted 1px;" >
92000-92003 &nbsp;

93300 &nbsp;


    <tr>
    <td style="border-bottom:#003 dotted 1px;" >
	
    <img src="http://www.teleco.com.br/imagens/logos/num_cel/Telecall.png" style="width:72px; height:72px;"  />
    </td>
    <td style="border-bottom:#003 dotted 1px;" >
93618 &nbsp;

94300 &nbsp;


    <tr>
    <td style="border-bottom:#003 dotted 1px;" >
	
    <img src="http://www.teleco.com.br/imagens/logos/num_cel/TIM.png" style="width:72px; height:72px;"  />
    </td>
    <td style="border-bottom:#003 dotted 1px;" >
98100-98165 &nbsp;

98167-98175 &nbsp;

98401-98409 &nbsp;

98411-98419 &nbsp;

98421-98429 &nbsp;

98431-98439 &nbsp;

98441-98449 &nbsp;

98451-98459 &nbsp;

98461-98469 &nbsp;

98471-98479 &nbsp;


    <tr>
    <td style="border-bottom:#003 dotted 1px;" >
	
    <img src="http://www.teleco.com.br/imagens/logos/num_cel/Unifique.png" style="width:72px; height:72px;"  />
    </td>
    <td style="border-bottom:#003 dotted 1px;" >
92200 &nbsp;


    <tr>
    <td style="border-bottom:#003 dotted 1px;" >
	
    <img src="http://www.teleco.com.br/imagens/logos/num_cel/Vivo.png" style="width:72px; height:72px;"  />
    </td>
    <td style="border-bottom:#003 dotted 1px;" >
99600-99665 &nbsp;

99667-99699 &nbsp;

99800-99850 &nbsp;

99900-99999 &nbsp;


</td>
<tr>

</table>
```

- [ ] **Step 2: Escrever os testes**

Create `tests/test_montar_tabela.py`:

```python
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from montar_tabela import parsear_faixas, escrever_csv, DDDS

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "ddd65.html")


def _ler_fixture() -> str:
    with open(FIXTURE, encoding="latin-1") as f:
        return f.read()


def test_parsear_faixas_extrai_todas_as_operadoras():
    resultado = parsear_faixas(_ler_fixture())
    operadoras = {r[0] for r in resultado}
    assert operadoras == {
        "Algar", "America Net", "Arqia", "Brisanet", "Claro",
        "Surf", "Telecall", "TIM", "Unifique", "Vivo",
    }


def test_parsear_faixas_vivo_tem_quatro_faixas():
    resultado = parsear_faixas(_ler_fixture())
    faixas_vivo = [(r[1], r[2]) for r in resultado if r[0] == "Vivo"]
    assert faixas_vivo == [
        (99600, 99665), (99667, 99699), (99800, 99850), (99900, 99999)
    ]


def test_parsear_faixas_valor_unico_sem_hifen():
    resultado = parsear_faixas(_ler_fixture())
    algar = [(r[1], r[2]) for r in resultado if r[0] == "Algar"]
    assert algar == [(96000, 96000)]


def test_parsear_faixas_valor_com_hifen_aberto():
    resultado = parsear_faixas(_ler_fixture())
    america_net = [(r[1], r[2]) for r in resultado if r[0] == "America Net"]
    assert america_net == [(93500, 93500)]


def test_parsear_faixas_tim_tem_dez_faixas():
    resultado = parsear_faixas(_ler_fixture())
    tim = [r for r in resultado if r[0] == "TIM"]
    assert len(tim) == 10


def test_escrever_csv(tmp_path):
    caminho = tmp_path / "saida.csv"
    dados = [("65", "Vivo", 99600, 99665), ("65", "TIM", 98100, 98165)]
    escrever_csv(dados, str(caminho))
    conteudo = caminho.read_text(encoding="utf-8")
    linhas = conteudo.strip().splitlines()
    assert linhas[0] == "ddd,operadora,prefixo_inicio,prefixo_fim"
    assert "65,Vivo,99600,99665" in linhas
    assert "65,TIM,98100,98165" in linhas


def test_ddds_tem_67_codigos_validos():
    assert len(DDDS) == 67
    assert 65 in DDDS
    assert 11 in DDDS
    assert 99 in DDDS
```

- [ ] **Step 3: Rodar os testes e confirmar que falham**

Run: `pytest tests/test_montar_tabela.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'montar_tabela'`.

- [ ] **Step 4: Implementar `montar_tabela.py`**

Create `montar_tabela.py`:

```python
"""Busca as faixas de numeração por operadora (fonte: Anatel, via Teleco)
e monta a tabela local `tabela_operadoras.csv`."""

import csv
import re
import urllib.parse
import urllib.request

ENDPOINT = "https://teleco.com.br/carrega_numeros_operadora.asp"

DDDS = [
    11, 12, 13, 14, 15, 16, 17, 18, 19,
    21, 22, 24, 27, 28,
    31, 32, 33, 34, 35, 37, 38,
    41, 42, 43, 44, 45, 46, 47, 48, 49,
    51, 53, 54, 55,
    61, 62, 63, 64, 65, 66, 67, 68, 69,
    71, 73, 74, 75, 77, 79,
    81, 82, 83, 84, 85, 86, 87, 88, 89,
    91, 92, 93, 94, 95, 96, 97, 98, 99,
]


def buscar_html_ddd(ddd: int) -> str:
    """Busca a tabela HTML de faixas de operadora para um DDD."""
    url = f"{ENDPOINT}?dd={ddd}"
    req = urllib.request.Request(url, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("latin-1")


def parsear_faixas(html_bruto: str) -> list[tuple[str, int, int]]:
    """Extrai (operadora, prefixo_inicio, prefixo_fim) do HTML retornado
    pelo endpoint. O nome da operadora vem do nome do arquivo de logo
    (ex: '.../num_cel/Vivo.png' -> 'Vivo')."""
    blocos = html_bruto.split("<tr>")[2:]  # pula texto antes da tabela e o cabeçalho
    resultado: list[tuple[str, int, int]] = []
    for bloco in blocos:
        m_img = re.search(r'num_cel/([^"]+)\.png', bloco)
        if not m_img:
            continue
        operadora = urllib.parse.unquote(m_img.group(1)).strip()
        for inicio_str, fim_str in re.findall(r"(\d{4,5})(?:-(\d{4,5}))?", bloco):
            inicio = int(inicio_str)
            fim = int(fim_str) if fim_str else inicio
            resultado.append((operadora, inicio, fim))
    return resultado


def escrever_csv(linhas: list[tuple[str, str, int, int]], caminho_saida: str) -> None:
    """Grava (ddd, operadora, prefixo_inicio, prefixo_fim) em CSV."""
    with open(caminho_saida, "w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(["ddd", "operadora", "prefixo_inicio", "prefixo_fim"])
        for ddd, operadora, inicio, fim in linhas:
            escritor.writerow([ddd, operadora, inicio, fim])


def gerar_tabela(caminho_saida: str = "tabela_operadoras.csv") -> None:
    """Busca as faixas de todos os DDDs e grava a tabela local completa."""
    linhas: list[tuple[str, str, int, int]] = []
    for ddd in DDDS:
        html_bruto = buscar_html_ddd(ddd)
        for operadora, inicio, fim in parsear_faixas(html_bruto):
            linhas.append((str(ddd), operadora, inicio, fim))
    escrever_csv(linhas, caminho_saida)


if __name__ == "__main__":
    gerar_tabela()
    print("tabela_operadoras.csv gerada.")
```

- [ ] **Step 5: Rodar os testes e confirmar que passam**

Run: `pytest tests/test_montar_tabela.py -v`
Expected: PASS em todos os testes.

- [ ] **Step 6: Commit**

```bash
git add montar_tabela.py tests/test_montar_tabela.py tests/fixtures/ddd65.html
git commit -m "feat: busca e parsing das faixas de operadora por DDD"
```

---

## Task 4: Script `classificar_planilha.py`

**Files:**
- Create: `classificar_planilha.py`
- Test: `tests/test_classificar_planilha.py`

**Interfaces:**
- Consumes:
  - `operadora.carregar_tabela(caminho_csv: str) -> dict[str, list[tuple[int, int, str]]]` (Task 2)
  - `operadora.normalizar_numero(numero) -> tuple[str, str] | None` (Task 2)
  - `operadora.identificar_operadora(ddd: str, assinante: str, tabela) -> str` (Task 2)
- Produces:
  - `classificar(caminho_entrada: str, coluna_telefone: str, caminho_tabela: str, caminho_saida: str) -> None`
  - CLI: `python classificar_planilha.py <entrada.xlsx> <coluna_telefone> <tabela.csv> <saida.xlsx>`

- [ ] **Step 1: Escrever o teste**

Create `tests/test_classificar_planilha.py`:

```python
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from classificar_planilha import classificar


def test_classificar_planilha_gera_coluna_operadora(tmp_path):
    entrada = tmp_path / "entrada.xlsx"
    saida = tmp_path / "saida.xlsx"
    tabela_csv = tmp_path / "tabela.csv"
    tabela_csv.write_text(
        "ddd,operadora,prefixo_inicio,prefixo_fim\n"
        "65,Vivo,99600,99665\n"
        "65,Vivo,99667,99699\n"
        "65,Vivo,99900,99999\n",
        encoding="utf-8",
    )
    pd.DataFrame(
        {
            "Nome": ["Ana", "Beto", "Carla", "Duda"],
            "Telefone": [
                "65999469686",
                "65996728854",
                "não é telefone",
                None,
            ],
        }
    ).to_excel(entrada, index=False)

    classificar(str(entrada), "Telefone", str(tabela_csv), str(saida))

    resultado = pd.read_excel(saida)
    assert list(resultado["Operadora"]) == [
        "Vivo",
        "Vivo",
        "Número inválido",
        "Vazio",
    ]
    # não deve alterar o arquivo de entrada
    entrada_relida = pd.read_excel(entrada)
    assert "Operadora" not in entrada_relida.columns


def test_classificar_planilha_prefixo_nao_mapeado(tmp_path):
    entrada = tmp_path / "entrada.xlsx"
    saida = tmp_path / "saida.xlsx"
    tabela_csv = tmp_path / "tabela.csv"
    tabela_csv.write_text(
        "ddd,operadora,prefixo_inicio,prefixo_fim\n"
        "65,Vivo,99600,99665\n",
        encoding="utf-8",
    )
    pd.DataFrame({"Telefone": ["65981112222"]}).to_excel(entrada, index=False)

    classificar(str(entrada), "Telefone", str(tabela_csv), str(saida))

    resultado = pd.read_excel(saida)
    assert list(resultado["Operadora"]) == ["Não identificado"]
```

- [ ] **Step 2: Rodar os testes e confirmar que falham**

Run: `pytest tests/test_classificar_planilha.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'classificar_planilha'`.

- [ ] **Step 3: Implementar `classificar_planilha.py`**

Create `classificar_planilha.py`:

```python
"""Lê uma planilha de contatos e grava uma cópia com a coluna Operadora."""

import sys

import pandas as pd

from operadora import carregar_tabela, identificar_operadora, normalizar_numero


def classificar(
    caminho_entrada: str, coluna_telefone: str, caminho_tabela: str, caminho_saida: str
) -> None:
    tabela = carregar_tabela(caminho_tabela)
    df = pd.read_excel(caminho_entrada)

    def classificar_linha(valor: object) -> str:
        if pd.isna(valor):
            return "Vazio"
        normalizado = normalizar_numero(valor)
        if normalizado is None:
            return "Número inválido"
        ddd, assinante = normalizado
        return identificar_operadora(ddd, assinante, tabela)

    df["Operadora"] = df[coluna_telefone].apply(classificar_linha)
    df.to_excel(caminho_saida, index=False)


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(
            "Uso: python classificar_planilha.py <entrada.xlsx> <coluna_telefone> "
            "<tabela.csv> <saida.xlsx>"
        )
        sys.exit(1)
    classificar(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    print(f"Planilha classificada salva em: {sys.argv[4]}")
```

- [ ] **Step 4: Rodar os testes e confirmar que passam**

Run: `pytest tests/test_classificar_planilha.py -v`
Expected: PASS em todos os testes.

- [ ] **Step 5: Commit**

```bash
git add classificar_planilha.py tests/test_classificar_planilha.py
git commit -m "feat: script principal de classificacao da planilha"
```

---

## Task 5: Execução real, validação end-to-end e instruções de uso

**Files:**
- Create: `README.md`
- Create (gerado, não versionado): `tabela_operadoras.csv`

**Interfaces:**
- Consumes: `montar_tabela.gerar_tabela()` (Task 3), `classificar_planilha.classificar()` (Task 4)
- Produces: nenhuma interface nova — esta task valida o pipeline completo
  com dados reais e documenta o uso para o usuário final.

- [ ] **Step 1: Rodar todos os testes automatizados juntos**

Run: `pytest -v`
Expected: todos os testes das Tasks 2, 3 e 4 passam.

- [ ] **Step 2: Gerar a tabela real a partir da Anatel/Teleco**

Run: `python montar_tabela.py`
Expected: mensagem `tabela_operadoras.csv gerada.` e o arquivo
`tabela_operadoras.csv` criado na raiz do projeto com uma linha por faixa de
cada DDD (deve ter centenas de linhas).

- [ ] **Step 3: Validar com os 3 números conhecidos**

Create um arquivo temporário `teste_manual.xlsx` com estas 3 linhas (coluna
`Telefone`): `65999469686`, `65996075347`, `65996728854`. Depois rode:

Run: `python classificar_planilha.py teste_manual.xlsx Telefone tabela_operadoras.csv teste_manual_saida.xlsx`

Expected: abrindo `teste_manual_saida.xlsx`, as 3 linhas devem mostrar
`Operadora = Vivo` — o mesmo resultado validado manualmente com o usuário
durante o brainstorming (ver spec, seção "Validação já feita").

- [ ] **Step 4: Escrever o README de uso**

Create `README.md`:

```markdown
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
```

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: instrucoes de uso do classificador de operadora"
```

---

## Self-Review

**Cobertura da spec:**
- Entrada Excel com coluna de telefone → Task 4 (`classificar`).
- Saída = cópia com coluna `Operadora`, original não alterado → Task 4,
  testado explicitamente (`entrada_relida` sem coluna `Operadora`).
- Fonte de dados Anatel via endpoint Teleco → Task 3 (`buscar_html_ddd`,
  `parsear_faixas`), com fixture real capturada durante o brainstorming.
- Tabela local reutilizável (`tabela_operadoras.csv`) → Task 3
  (`gerar_tabela`, `escrever_csv`) + Task 2 (`carregar_tabela`).
- Lógica de faixa (5 primeiros dígitos do assinante) → Task 2
  (`identificar_operadora`), testada com os 3 números reais validados na
  spec.
- Tratamento de erros: número inválido, não identificado, célula vazia →
  Task 4, todos os 4 casos cobertos no teste.
- Validação end-to-end com os 3 números conhecidos → Task 5, Step 3.
- README para o usuário final → Task 5, Step 4.

**Placeholder scan:** nenhum "TBD"/"TODO" — todos os steps têm código
completo ou comando exato.

**Consistência de tipos:** `carregar_tabela` retorna
`dict[str, list[tuple[int, int, str]]]` na Task 2 e é consumida exatamente
nesse formato em `identificar_operadora` (Task 2) e em `classificar` (Task 4).
`normalizar_numero` retorna `tuple[str, str] | None` na Task 2 e
`classificar_planilha.py` trata o caso `None` explicitamente. Nomes de função
conferem em todas as tasks que os consomem.
