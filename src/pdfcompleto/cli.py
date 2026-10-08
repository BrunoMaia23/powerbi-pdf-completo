"""Ferramentas do PDF completo: dados do modelo fictício, URL do paginado, divisão e validação."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from . import dados, distribuicao, url, validar


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(prog="pdfcompleto", description=__doc__)
    sub = parser.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("dados", help="gera os CSVs do modelo fictício")
    p.add_argument("--pasta", type=Path, default=Path("modelo"))

    p = sub.add_parser("esperado", help="grava o resultado esperado da consulta para um filtro")
    p.add_argument("--pasta", type=Path, default=Path("modelo"))
    p.add_argument("--ano", type=int)
    p.add_argument("--vendedor", type=int, action="append")
    p.add_argument("--saida", type=Path, default=Path("esperado.csv"))

    p = sub.add_parser("url", help="monta a URL do relatório paginado para um filtro")
    p.add_argument("--base", required=True)
    p.add_argument("--ano", type=int)
    p.add_argument("--vendedor", type=int, action="append")

    p = sub.add_parser("distribuir", help="mostra como o filtro se reparte nas tabelas da página de PDF")
    p.add_argument("--pasta", type=Path, default=Path("modelo"))
    p.add_argument("--ano", type=int)
    p.add_argument("--vendedor", type=int, action="append")
    p.add_argument("--tabelas", type=int, default=4)
    p.add_argument("--linhas-por-tabela", type=int, default=300)

    p = sub.add_parser("validar", help="confere um PDF exportado contra o CSV esperado")
    p.add_argument("pdf", type=Path)
    p.add_argument("esperado", type=Path)

    a = parser.parse_args(argv)
    if a.comando == "dados":
        print(dados.gerar(a.pasta))
    elif a.comando == "esperado":
        linhas = dados.esperado(a.pasta, a.ano, set(a.vendedor) if a.vendedor else None)
        with open(a.saida, "w", encoding="utf-8", newline="") as f:
            escritor = csv.DictWriter(f, fieldnames=["codigo", "descricao", "grupo", "valor"], extrasaction="ignore")
            escritor.writeheader()
            escritor.writerows(linhas)
        print(f"{len(linhas)} itens em {a.saida}")
    elif a.comando == "url":
        endereco = url.montar(a.base, a.ano, a.vendedor)
        print(endereco)
        if not url.cabe(endereco):
            print(f"atenção: {len(endereco)} caracteres, acima de {url.LIMITE_URL}", file=sys.stderr)
            return 1
    elif a.comando == "distribuir":
        linhas = dados.esperado(a.pasta, a.ano, set(a.vendedor) if a.vendedor else None)
        d = distribuicao.distribuir([l["codigo"] for l in linhas], a.tabelas, a.linhas_por_tabela)
        print(f"{len(linhas)} itens, {d.por_tabela} por tabela, {d.escondidas} escondidos")
        if d.aviso:
            print(d.aviso)
    elif a.comando == "validar":
        r = validar.conferir(a.pdf, validar.ler_esperado(a.esperado))
        print(f"{r.conferidos} itens conferidos | faltando {len(r.faltando)} | sobrando {len(r.sobrando)} | "
              f"repetidos {len(r.repetidos)} | valor diferente {len(r.valor_diferente)}")
        for codigo, esperado, no_pdf in r.valor_diferente[:20]:
            print(f"   {codigo}: esperado {esperado}, no PDF {no_pdf}")
        if r.faltando:
            print(f"   faltando: {r.faltando[:20]}")
        print("OK: o PDF tem todos os itens, com os valores certos." if r.ok else "O PDF NÃO bate com o esperado.")
        return 0 if r.ok else 1
    return 0
