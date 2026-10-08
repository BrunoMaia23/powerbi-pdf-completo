"""Confere um PDF exportado contra o resultado esperado da consulta, item a item.

A extração de texto de tabelas lado a lado mistura as colunas numa mesma linha, então a busca não
depende da ordem: cada ocorrência de "código descrição valor" é lida onde estiver. Valores no
formato brasileiro (1.234,56).
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from pypdf import PdfReader

ITEM = re.compile(r"(?<!\d)(\d{4})\s+([^\d\n]+?)\s+(-?\d{1,3}(?:\.\d{3})*,\d{2})(?!\d)")


@dataclass
class Resultado:
    conferidos: int = 0
    faltando: list[int] = field(default_factory=list)
    sobrando: list[int] = field(default_factory=list)
    repetidos: list[int] = field(default_factory=list)
    valor_diferente: list[tuple[int, Decimal, Decimal]] = field(default_factory=list)  # (código, esperado, no PDF)

    @property
    def ok(self) -> bool:
        return not (self.faltando or self.sobrando or self.repetidos or self.valor_diferente)


def numero_br(texto: str) -> Decimal:
    return Decimal(texto.replace(".", "").replace(",", "."))


def itens_do_pdf(caminho: Path | str) -> list[tuple[int, str, Decimal]]:
    texto = "\n".join(pagina.extract_text() or "" for pagina in PdfReader(str(caminho)).pages)
    return [(int(c), d.strip(), numero_br(v)) for c, d, v in ITEM.findall(texto)]


def conferir(pdf: Path | str, esperado: list[dict]) -> Resultado:
    """`esperado`: linhas com codigo e valor (Decimal ou texto com ponto decimal)."""
    encontrados = itens_do_pdf(pdf)
    no_pdf: dict[int, Decimal] = {}
    r = Resultado()
    for codigo, _, valor in encontrados:
        if codigo in no_pdf:
            r.repetidos.append(codigo)
        no_pdf[codigo] = valor
    alvo = {int(l["codigo"]): Decimal(str(l["valor"])) for l in esperado}
    r.faltando = sorted(set(alvo) - set(no_pdf))
    r.sobrando = sorted(set(no_pdf) - set(alvo))
    for codigo in sorted(set(alvo) & set(no_pdf)):
        r.conferidos += 1
        if alvo[codigo] != no_pdf[codigo]:
            r.valor_diferente.append((codigo, alvo[codigo], no_pdf[codigo]))
    return r


def ler_esperado(caminho: Path | str) -> list[dict]:
    """CSV com o resultado da consulta DAX (colunas codigo e valor, ponto como separador decimal)."""
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))
