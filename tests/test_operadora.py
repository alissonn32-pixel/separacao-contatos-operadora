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
