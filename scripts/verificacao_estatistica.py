"""Verificação independente das comparações pareadas de aceitação contra o PETIC.

Reimplementa, sem reutilizar scripts/paired_analysis.py, as estatísticas por
(topologia, nível, algoritmo): média e mediana das diferenças pareadas por
cenário (p.p.), p-valor EXATO do teste de postos sinalizados de Wilcoxon (por
programação dinâmica sobre os postos médios dobrados, com empates), teste do
sinal exato, IC95% bootstrap percentil (semente própria) e ajuste de Holm sobre
todas as comparações. Em seguida compara com analise_pareada_aceitacao.csv
(se existir) e imprime as divergências de média, de p-valor e de decisão.

Uso: python3.11 -m scripts.verificacao_estatistica --run results/<execução>
Só stdlib. Não altera nenhum arquivo existente: grava verificacao_estatistica.csv.
"""
from __future__ import annotations

import argparse
import csv
import math
import random
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
from statistics import median


def postos_medios_dobrados(valores_abs: list[float]) -> list[int]:
    """Postos médios multiplicados por 2 (inteiros), tratando empates."""
    ordem = sorted(range(len(valores_abs)), key=lambda i: valores_abs[i])
    postos = [0] * len(valores_abs)
    i = 0
    while i < len(ordem):
        j = i
        while j + 1 < len(ordem) and valores_abs[ordem[j + 1]] == valores_abs[ordem[i]]:
            j += 1
        medio_dobrado = (i + 1) + (j + 1)  # 2 * média de (i+1..j+1)
        for k in range(i, j + 1):
            postos[ordem[k]] = medio_dobrado
        i = j + 1
    return postos


def wilcoxon_exato(diferencas: list[float]) -> tuple[float, int]:
    """p bicaudal exato condicional aos postos observados (zeros descartados)."""
    d = [x for x in diferencas if x != 0]
    n = len(d)
    if n == 0:
        return 1.0, 0
    postos = postos_medios_dobrados([abs(x) for x in d])
    total = sum(postos)
    w_mais = sum(p for p, x in zip(postos, d) if x > 0)
    # Distribuição de W+ sob H0: cada posto entra com prob. 1/2.
    ways = [0] * (total + 1)
    ways[0] = 1
    for p in postos:
        for s in range(total, p - 1, -1):
            ways[s] += ways[s - p]
    todos = 2 ** n
    cauda = lambda a, b: sum(ways[a:b + 1])
    menor = min(w_mais, total - w_mais)
    p = Fraction(2 * cauda(0, menor), todos)
    return float(min(Fraction(1), p)), n


def sinal_exato(diferencas: list[float]) -> float:
    pos = sum(1 for x in diferencas if x > 0)
    neg = sum(1 for x in diferencas if x < 0)
    n = pos + neg
    if n == 0:
        return 1.0
    k = min(pos, neg)
    p = Fraction(2 * sum(math.comb(n, i) for i in range(k + 1)), 2 ** n)
    return float(min(Fraction(1), p))


def bootstrap_ic(diferencas: list[float], rng: random.Random, b: int = 5000):
    n = len(diferencas)
    medias = sorted(sum(rng.choices(diferencas, k=n)) / n for _ in range(b))
    return medias[int(0.025 * b)], medias[min(b - 1, int(0.975 * b))]


def holm(pvalores: list[float]) -> list[float]:
    m = len(pvalores)
    ordem = sorted(range(m), key=lambda i: pvalores[i])
    ajustado = [1.0] * m
    maior = 0.0
    for posto, i in enumerate(ordem):
        maior = max(maior, (m - posto) * pvalores[i])
        ajustado[i] = min(1.0, maior)
    return ajustado


def carregar(run: Path):
    grupos = defaultdict(dict)
    with (run / "todas_execucoes.csv").open(encoding="utf-8", newline="") as fh:
        for linha in csv.DictReader(fh):
            if linha.get("scope") != "summary":
                continue
            chave = (linha["topology"], linha["load_level"], linha["scenario_id"])
            grupos[chave][linha["algorithm"]] = float(linha["acceptance.acceptance_percent"])
    return grupos


def verificar(run: Path, bootstrap: int = 5000, seed: int = 987654321):
    grupos = carregar(run)
    rng = random.Random(seed)
    linhas = []
    celulas = sorted({(t, n) for t, n, _ in grupos})
    for topo, nivel in celulas:
        cenarios = [a for (t, n, _), a in grupos.items()
                    if t == topo and n == nivel and "petic" in a]
        for alg in ("aco", "q-learning", "sa"):
            dif = [a[alg] - a["petic"] for a in cenarios if alg in a]
            if len(dif) < 2:
                continue
            p, n_efetivo = wilcoxon_exato(dif)
            lo, hi = bootstrap_ic(dif, rng, bootstrap)
            linhas.append({
                "topology": topo, "load_level": nivel, "algorithm": alg,
                "n_scenarios": len(dif), "n_nonzero": n_efetivo,
                "mean_difference_pp": sum(dif) / len(dif),
                "median_difference_pp": median(dif),
                "bootstrap_ci95_low": lo, "bootstrap_ci95_high": hi,
                "wilcoxon_exact_p": p, "sign_exact_p": sinal_exato(dif),
            })
    for linha, h in zip(linhas, holm([l["wilcoxon_exact_p"] for l in linhas])):
        linha["wilcoxon_exact_holm"] = h
    saida = run / "verificacao_estatistica.csv"
    with saida.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    return linhas, saida


def comparar(run: Path, linhas):
    ref = run / "analise_pareada_aceitacao.csv"
    if not ref.exists():
        print("analise_pareada_aceitacao.csv não encontrado: nada a comparar.")
        return
    with ref.open(encoding="utf-8", newline="") as fh:
        outras = {(r["topology"], r["load_level"], r["algorithm"]): r
                  for r in csv.DictReader(fh)}
    max_media = max_p = 0.0
    div_decisao = []
    for l in linhas:
        o = outras.get((l["topology"], l["load_level"], l["algorithm"]))
        if o is None:
            print("ausente na análise do Codex:", l["topology"], l["load_level"], l["algorithm"])
            continue
        max_media = max(max_media, abs(l["mean_difference_pp"] - float(o["mean_difference_pp"])))
        max_p = max(max_p, abs(l["wilcoxon_exact_p"] - float(o["wilcoxon_p"])))
        a = l["wilcoxon_exact_holm"] < 0.05
        b = float(o["wilcoxon_holm"]) < 0.05
        if a != b:
            div_decisao.append((l["topology"], l["load_level"], l["algorithm"],
                                l["wilcoxon_exact_holm"], float(o["wilcoxon_holm"])))
    print(f"{len(linhas)} comparações verificadas.")
    print(f"maior diferença absoluta na média (p.p.): {max_media:.2e}")
    print(f"maior diferença absoluta no p bicaudal (exato x normal c/ correção): {max_p:.3f}")
    print(f"divergências na decisão após Holm (alfa 0,05): {len(div_decisao)}")
    for d in div_decisao:
        print("  ", d)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--bootstrap", type=int, default=5000)
    args = parser.parse_args(argv)
    linhas, saida = verificar(args.run, args.bootstrap)
    print(saida)
    comparar(args.run, linhas)


if __name__ == "__main__":
    main()
