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
