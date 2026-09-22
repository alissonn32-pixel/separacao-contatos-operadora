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
