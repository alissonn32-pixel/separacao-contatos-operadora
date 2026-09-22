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
