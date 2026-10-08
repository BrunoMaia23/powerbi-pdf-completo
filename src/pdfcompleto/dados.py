"""Modelo fictício de extrato de comissões: vendedores, itens agrupados e lançamentos por ano."""
from __future__ import annotations

import csv
import random
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

GRUPOS = [  # (ordem, nome, descrições dos itens)
    (1, "Vendas diretas", ["Linha casa", "Linha escritório", "Linha jardim", "Linha cozinha", "Linha banho"]),
    (2, "Vendas por indicação", ["Indicação de cliente", "Indicação de revenda", "Parceria regional"]),
    (3, "Bônus", ["Meta trimestral", "Meta anual", "Campanha de lançamento", "Fidelização"]),
    (4, "Ajustes", ["Estorno de venda", "Devolução", "Correção de tabela", "Arredondamento"]),
]
REGIONAIS = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
NOMES = ["Ana", "Bruna", "Caio", "Diego", "Elisa", "Felipe", "Gabi", "Heitor", "Isis", "Jonas", "Kátia", "Lucas"]
SOBRENOMES = ["Araújo", "Batista", "Cardoso", "Dias", "Freitas", "Lima", "Mendes", "Pires", "Rezende", "Torres"]
CENTAVO = Decimal("0.01")


def itens() -> list[dict]:
    """Os itens do extrato, cada um com código, grupo e uma chave de ordenação única."""
    resultado = []
    for ordem, grupo, descricoes in GRUPOS:
        for variante in ("", " especial", " premium", " regional", " online", " atacado"):
            for descricao in descricoes:
                codigo = 1000 * ordem + len([i for i in resultado if i["ordem_grupo"] == ordem]) + 1
                resultado.append({"codigo": codigo, "descricao": descricao + variante, "grupo": grupo,
                                  "ordem_grupo": ordem, "chave_ordem": ordem * 10_000 + codigo % 1000})
    return resultado


def gerar(destino: Path | str, semente: int = 11, vendedores: int = 40) -> dict[str, int]:
    """Grava os CSVs do modelo (o que um modelo semântico carregaria) e devolve as linhas de cada um."""
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    rng = random.Random(semente)
    lista_itens = itens()
    lista_vendedores = [{"vendedor_id": i, "nome": f"{rng.choice(NOMES)} {rng.choice(SOBRENOMES)}",
                         "regional": rng.choice(REGIONAIS)} for i in range(1, vendedores + 1)]
    lancamentos = []
    for v in lista_vendedores:
        for ano in (2024, 2025):
            # cada vendedor tem uma parte dos itens; alguns poucos têm quase todos
            fatia = rng.uniform(0.85, 1.0) if v["vendedor_id"] % 13 == 0 else rng.uniform(0.05, 0.35)
            for item in rng.sample(lista_itens, max(1, int(len(lista_itens) * fatia))):
                sinal = -1 if item["ordem_grupo"] == 4 and item["descricao"].startswith(("Estorno", "Devolução")) else 1
                valor = Decimal(str(rng.uniform(5, 4_000))).quantize(CENTAVO) * sinal
                lancamentos.append({"ano": ano, "vendedor_id": v["vendedor_id"], "codigo": item["codigo"], "valor": valor})
    _csv(destino / "dim_item.csv", lista_itens)
    _csv(destino / "dim_vendedor.csv", lista_vendedores)
    _csv(destino / "fato_comissao.csv", lancamentos)
    return {"dim_item": len(lista_itens), "dim_vendedor": len(lista_vendedores), "fato_comissao": len(lancamentos)}


def esperado(pasta: Path | str, ano: int | None = None, vendedores: set[int] | None = None) -> list[dict]:
    """O que a consulta do relatório paginado devolve para um filtro: total por item, na ordem do extrato."""
    pasta = Path(pasta)
    por_codigo = {int(i["codigo"]): i for i in _ler(pasta / "dim_item.csv")}
    soma: dict[int, Decimal] = defaultdict(Decimal)
    for l in _ler(pasta / "fato_comissao.csv"):
        if (ano is None or int(l["ano"]) == ano) and (vendedores is None or int(l["vendedor_id"]) in vendedores):
            soma[int(l["codigo"])] += Decimal(l["valor"])
    linhas = [{"codigo": c, "descricao": por_codigo[c]["descricao"], "grupo": por_codigo[c]["grupo"],
               "chave_ordem": int(por_codigo[c]["chave_ordem"]), "valor": v.quantize(CENTAVO, ROUND_HALF_UP)}
              for c, v in soma.items()]
    return sorted(linhas, key=lambda l: l["chave_ordem"])


def _csv(arquivo: Path, linhas: list[dict]) -> None:
    with open(arquivo, "w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=list(linhas[0]))
        escritor.writeheader()
        escritor.writerows(linhas)


def _ler(arquivo: Path) -> list[dict]:
    with open(arquivo, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))
