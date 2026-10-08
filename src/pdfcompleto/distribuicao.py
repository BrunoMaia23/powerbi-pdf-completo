"""Divisão dos itens do filtro entre as tabelas lado a lado da página de PDF.

Espelha as medidas `Linha no PDF` e `Tabela no PDF` (dax/medidas_pagina_pdf.dax): cada item com valor
ganha a sua posição na ordem do extrato, e as posições são repartidas em blocos iguais entre as
tabelas. A página tem altura fixa, então cada tabela mostra no máximo `linhas_por_tabela` linhas; o
que passar disso fica escondido, e por isso o aviso.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Distribuicao:
    tabela_de: dict[int, int]   # código do item -> tabela (1..n)
    por_tabela: int             # linhas em cada tabela
    escondidas: int             # linhas que não cabem na altura da página
    aviso: str | None


def distribuir(codigos_em_ordem: list[int], tabelas: int = 4, linhas_por_tabela: int = 300) -> Distribuicao:
    if tabelas < 1 or linhas_por_tabela < 1:
        raise ValueError("tabelas e linhas_por_tabela precisam ser positivos")
    n = len(codigos_em_ordem)
    por_tabela = max(1, math.ceil(n / tabelas))
    tabela_de = {codigo: min(tabelas, math.ceil(posicao / por_tabela))
                 for posicao, codigo in enumerate(codigos_em_ordem, start=1)}
    linhas = [sum(1 for t in tabela_de.values() if t == k) for k in range(1, tabelas + 1)]
    escondidas = sum(max(0, l - linhas_por_tabela) for l in linhas)
    capacidade = tabelas * linhas_por_tabela
    aviso = (f"O filtro tem {n} itens e a página mostra no máximo {capacidade}. "
             "Use o PDF completo (relatório paginado).") if n > capacidade else None
    return Distribuicao(tabela_de, por_tabela, escondidas, aviso)
