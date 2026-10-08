"""URL que abre o relatório paginado já filtrado e exportado em PDF.

É a mesma lógica da medida `URL do PDF completo` (dax/url_pdf_completo.dax), escrita em Python para
poder ser testada. Os filtros vão por ID, nunca por nome: número não precisa de escape na URL, e a
medida DAX não tem uma função de URL-encode.
"""
from __future__ import annotations

TODOS = "TODOS"          # sem filtro de vendedor: a consulta do paginado entende como "todos"
LIMITE_URL = 1_800       # acima disso o navegador ou o serviço podem truncar a URL


def montar(base: str, ano: int | None, vendedores: list[int] | None, formato: str = "PDF") -> str:
    partes = [f"{base}?rdl:format={formato}"]
    if ano is not None:
        partes.append(f"rp:Ano={int(ano)}")
    if vendedores:
        partes += [f"rp:Vendedores={int(v)}" for v in sorted(set(vendedores))]
    else:
        partes.append(f"rp:Vendedores={TODOS}")
    return "&".join(partes)


def cabe(url: str) -> bool:
    return len(url) <= LIMITE_URL
