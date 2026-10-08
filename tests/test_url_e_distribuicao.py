import pytest

from pdfcompleto import distribuicao, url

BASE = "https://app.powerbi.com/groups/me/rdlreports/ID-DO-RELATORIO-PAGINADO"


def test_url_com_ano_e_vendedores_em_ordem_e_sem_repeticao():
    # é exatamente o que a medida DAX monta: CONCATENATEX ordenado por vendedor_id
    assert url.montar(BASE, 2025, [7, 3, 7]) == f"{BASE}?rdl:format=PDF&rp:Ano=2025&rp:Vendedores=3&rp:Vendedores=7"


def test_url_sem_filtro_de_vendedor_manda_todos():
    assert url.montar(BASE, 2025, None).endswith("&rp:Vendedores=TODOS")
    assert url.montar(BASE, 2025, []).endswith("&rp:Vendedores=TODOS")


def test_url_sem_ano_deixa_o_paginado_usar_todos_os_anos():
    assert "rp:Ano" not in url.montar(BASE, None, [1])


def test_url_longa_demais():
    assert url.cabe(url.montar(BASE, 2025, list(range(1, 50))))
    assert not url.cabe(url.montar(BASE, 2025, list(range(1, 200))))


def test_divisao_em_blocos_continuos():
    d = distribuicao.distribuir(list(range(101, 113)), tabelas=4, linhas_por_tabela=10)  # 12 itens
    assert d.por_tabela == 3
    assert [d.tabela_de[c] for c in range(101, 113)] == [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4]
    assert d.escondidas == 0 and d.aviso is None


def test_ultima_tabela_fica_com_o_resto():
    d = distribuicao.distribuir(list(range(1, 12)), tabelas=4, linhas_por_tabela=10)  # 11 itens, 3 por tabela
    assert sorted(d.tabela_de.values()).count(4) == 2 and 5 not in d.tabela_de.values()


def test_filtro_maior_que_a_pagina_avisa_e_conta_o_que_some():
    d = distribuicao.distribuir(list(range(1, 61)), tabelas=4, linhas_por_tabela=10)  # 60 itens, cabem 40
    assert d.por_tabela == 15
    assert d.escondidas == 20
    assert "60 itens" in d.aviso and "no máximo 40" in d.aviso


def test_parametros_invalidos():
    with pytest.raises(ValueError):
        distribuicao.distribuir([1], tabelas=0)
