import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from pdfcompleto import dados

RAIZ = Path(__file__).resolve().parents[1]
NS = {"r": "http://schemas.microsoft.com/sqlserver/reporting/2016/01/reportdefinition"}
RDL = ET.parse(RAIZ / "rdl" / "extrato_completo.rdl").getroot()


def _textos(caminho):
    return [e.text or "" for e in RDL.iterfind(caminho, NS)]


def test_parametros_do_relatorio_chegam_na_consulta():
    relatorio = {p.get("Name") for p in RDL.iterfind(".//r:ReportParameter", NS)}
    consulta = {p.get("Name") for p in RDL.iterfind(".//r:QueryParameter", NS)}
    comando = _textos(".//r:CommandText")[0]
    assert relatorio == consulta == {"Ano", "Vendedores"}
    assert all(f"@{p}" in comando for p in consulta)


def test_consulta_do_rdl_e_a_do_arquivo_dax_sao_a_mesma():
    arquivo = (RAIZ / "dax" / "consulta_paginado.dax").read_text(encoding="utf-8")
    sem_comentarios = "\n".join(l for l in arquivo.splitlines() if not l.startswith("//")).strip()
    assert " ".join(sem_comentarios.split()) == " ".join(_textos(".//r:CommandText")[0].split())


def test_campos_usados_existem_no_dataset_e_na_consulta():
    campos = {f.get("Name"): f.find("r:DataField", NS).text for f in RDL.iterfind(".//r:Field", NS)}
    usados = set(re.findall(r"Fields!(\w+)\.Value", " ".join(_textos(".//r:Value") + _textos(".//r:GroupExpression"))))
    assert usados <= set(campos)
    comando = _textos(".//r:CommandText")[0]
    for coluna in campos.values():
        assert coluna.split("[")[-1].rstrip("]") in comando


def test_pagina_a4_e_numeros_em_portugues():
    assert _textos(".//r:Language") == ["pt-BR"]
    assert _textos(".//r:PageWidth") == ["21cm"] and _textos(".//r:PageHeight") == ["29.7cm"]
    largura_util = 21 - 2 - 2
    assert float(_textos(".//r:ReportSection/r:Width")[0].rstrip("cm")) <= largura_util


@pytest.mark.skipif(not os.environ.get("RDL_XSD"), reason="defina RDL_XSD com o schema 2016/01 do RDL")
def test_rdl_valido_pelo_schema_oficial():
    from lxml import etree
    esquema = etree.XMLSchema(etree.parse(os.environ["RDL_XSD"]))
    assert esquema.validate(etree.parse(str(RAIZ / "rdl" / "extrato_completo.rdl"))), esquema.error_log


def test_dados_ficticios_deterministicos(tmp_path):
    assert dados.gerar(tmp_path / "a") == dados.gerar(tmp_path / "b")
    assert (tmp_path / "a" / "fato_comissao.csv").read_bytes() == (tmp_path / "b" / "fato_comissao.csv").read_bytes()


def test_descricoes_sem_digitos_e_chave_de_ordem_unica():
    itens = dados.itens()
    assert all(not any(ch.isdigit() for ch in i["descricao"]) for i in itens)  # o validador depende disso
    assert len({i["chave_ordem"] for i in itens}) == len(itens)
    assert [i["chave_ordem"] for i in itens] == sorted(i["chave_ordem"] for i in itens)


def test_esperado_soma_por_item_no_filtro(tmp_path):
    dados.gerar(tmp_path)
    todos = dados.esperado(tmp_path)
    um_ano = dados.esperado(tmp_path, ano=2025)
    um_vendedor = dados.esperado(tmp_path, ano=2025, vendedores={13})
    assert len(um_vendedor) <= len(um_ano) <= len(todos) <= len(dados.itens())
    assert [l["chave_ordem"] for l in um_ano] == sorted(l["chave_ordem"] for l in um_ano)
