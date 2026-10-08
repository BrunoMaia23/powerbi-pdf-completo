"""O validador lido contra PDFs gerados aqui mesmo, com o layout da página de PDF (tabelas lado a
lado). São PDFs sintéticos feitos com fpdf2, não exportações do Power BI."""
import math
from decimal import Decimal

import pytest
from fpdf import FPDF

from pdfcompleto import dados, validar


def numero(valor: Decimal) -> str:
    texto = f"{valor:,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def pdf_em_tabelas(caminho, linhas, tabelas=4):
    pdf = FPDF(orientation="L", format="A3")
    pdf.add_page()
    pdf.set_font("helvetica", size=6)
    por_tabela = max(1, math.ceil(len(linhas) / tabelas))
    largura = 80
    for k in range(tabelas):
        bloco = linhas[k * por_tabela:(k + 1) * por_tabela]
        for i, l in enumerate(bloco):
            pdf.set_xy(10 + k * largura, 10 + i * 3.2)
            pdf.cell(10, 3, str(l["codigo"]))
            pdf.cell(52, 3, l["descricao"])
            pdf.cell(14, 3, numero(Decimal(str(l["valor"]))), align="R")
    pdf.output(str(caminho))


@pytest.fixture(scope="module")
def esperado(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("modelo")
    dados.gerar(pasta)
    return dados.esperado(pasta, ano=2025)


def test_numero_brasileiro():
    assert validar.numero_br("1.234,56") == Decimal("1234.56")
    assert validar.numero_br("-12,30") == Decimal("-12.30")


def test_pdf_completo_bate(tmp_path, esperado):
    pdf_em_tabelas(tmp_path / "ok.pdf", esperado)
    r = validar.conferir(tmp_path / "ok.pdf", esperado)
    assert r.ok and r.conferidos == len(esperado)


def test_pdf_cortado_e_com_valor_errado(tmp_path, esperado):
    errado = [dict(l) for l in esperado]
    sumido = errado.pop(len(errado) // 2)                          # a linha que a rolagem escondeu
    errado[0]["valor"] = Decimal(str(errado[0]["valor"])) + Decimal("0.01")
    pdf_em_tabelas(tmp_path / "ruim.pdf", errado)
    r = validar.conferir(tmp_path / "ruim.pdf", esperado)
    assert not r.ok
    assert r.faltando == [sumido["codigo"]]
    assert [c for c, _, _ in r.valor_diferente] == [errado[0]["codigo"]]


def test_item_que_nao_devia_estar_no_pdf(tmp_path, esperado):
    pdf_em_tabelas(tmp_path / "a_mais.pdf", esperado)
    r = validar.conferir(tmp_path / "a_mais.pdf", esperado[1:])
    assert r.sobrando == [esperado[0]["codigo"]]
