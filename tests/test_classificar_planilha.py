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


def test_classificar_planilha_entrada_csv_ponto_e_virgula_saida_csv(tmp_path):
    entrada = tmp_path / "entrada.csv"
    saida = tmp_path / "saida.csv"
    tabela_csv = tmp_path / "tabela.csv"
    tabela_csv.write_text(
        "ddd,operadora,prefixo_inicio,prefixo_fim\n"
        "67,Claro,99700,99799\n",
        encoding="utf-8",
    )
    entrada.write_text(
        "Name;Phone 1 - Value;Group Membership\n"
        "Contato 1;5567997123456;TempOperadora\n",
        encoding="utf-8",
    )

    classificar(str(entrada), "Phone 1 - Value", str(tabela_csv), str(saida))

    resultado = pd.read_csv(saida)
    assert list(resultado["Operadora"]) == ["Claro"]
    # não deve alterar o arquivo de entrada
    entrada_relida = pd.read_csv(str(entrada), sep=";")
    assert "Operadora" not in entrada_relida.columns
