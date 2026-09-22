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
