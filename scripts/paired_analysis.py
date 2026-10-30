"""Comparações pareadas de aceitação por cenário contra o PETIC.

Uso: python3.11 -m scripts.paired_analysis --run results/<execução>
Produz diferenças em pontos percentuais, IC bootstrap, Wilcoxon com Holm e
correlação bisserial por postos como tamanho de efeito.
"""

from __future__ import annotations

import argparse
import csv
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median


def _postos_com_empate(valores: list[float]) -> list[float]:
    ordenados = sorted(enumerate(abs(v) for v in valores), key=lambda par: par[1])
    postos = [0.0] * len(valores)
    inicio = 0
    while inicio < len(ordenados):
        fim = inicio + 1
        while fim < len(ordenados) and ordenados[fim][1] == ordenados[inicio][1]:
            fim += 1
        posto_medio = ((inicio + 1) + fim) / 2
        for pos in range(inicio, fim):
            postos[ordenados[pos][0]] = posto_medio
        inicio = fim
    return postos


def _wilcoxon_pvalue(diferencas: list[float]) -> float:
    """p bicaudal por aproximação normal do teste de postos sinalizados."""
    pares = [(d, abs(d)) for d in diferencas if d != 0]
    n = len(pares)
    if n == 0:
        return 1.0
    valores = [d for d, _ in pares]
    postos = _postos_com_empate(valores)
    w_mais = sum(p for p, d in zip(postos, valores) if d > 0)
    media = n * (n + 1) / 4
    frequencias = Counter(abs(d) for d in valores)
    correcao_empates = sum(t ** 3 - t for t in frequencias.values()) / 48
    variancia = n * (n + 1) * (2 * n + 1) / 24 - correcao_empates
    if variancia <= 0:
        return 1.0
    delta = w_mais - media
    z = max(0.0, abs(delta) - 0.5) / math.sqrt(variancia)
    return math.erfc(z / math.sqrt(2))


def analisar(run: Path, *, bootstrap: int = 10000, seed: int = 20261030) -> Path:
    if bootstrap < 1:
        raise ValueError("bootstrap deve ser positivo")
    arquivo = run / "todas_execucoes.csv"
    grupos = defaultdict(dict)
    with arquivo.open(encoding="utf-8", newline="") as fluxo:
        for linha in csv.DictReader(fluxo):
            if linha.get("scope") != "summary":
                continue
            chave = (linha["topology"], linha["load_level"], linha["scenario_id"])
            grupos[chave][linha["algorithm"]] = float(
                linha["acceptance.acceptance_percent"]
            )

    comparacoes = []
    for topo, nivel in sorted({(t, n) for t, n, _ in grupos}):
        cenarios = [
            algs for (t, n, _), algs in grupos.items()
            if t == topo and n == nivel and "petic" in algs
        ]
        for algoritmo in ("aco", "q-learning", "sa"):
            pares = [(a[algoritmo] - a["petic"]) for a in cenarios
                     if algoritmo in a]
            if len(pares) < 2:
                continue
            p = _wilcoxon_pvalue(pares)
            positivos = [d for d in pares if d != 0]
            ranks = _postos_com_empate(positivos)
            soma_pos = sum(r for r, d in zip(ranks, positivos) if d > 0)
            soma_neg = sum(r for r, d in zip(ranks, positivos) if d < 0)
            efeito = (soma_pos - soma_neg) / (soma_pos + soma_neg) if ranks else 0.0
            comparacoes.append({
                "topology": topo, "load_level": nivel, "algorithm": algoritmo,
                "n_scenarios": len(pares), "mean_difference_pp": sum(pares) / len(pares),
                "median_difference_pp": median(pares),
                "wilcoxon_p": p, "rank_biserial": efeito, "differences": pares,
            })

    # Ajuste Holm único sobre 54 comparações (3 algoritmos x 18 células).
    ordenadas = sorted(range(len(comparacoes)), key=lambda i: comparacoes[i]["wilcoxon_p"])
    ajustados = [1.0] * len(comparacoes)
    maior = 0.0
    m = len(comparacoes)
    for posto, indice in enumerate(ordenadas):
        maior = max(maior, (m - posto) * comparacoes[indice]["wilcoxon_p"])
        ajustados[indice] = min(1.0, maior)

    rng = random.Random(seed)
    for i, comparacao in enumerate(comparacoes):
        valores = comparacao.pop("differences")
        medias = []
        for _ in range(bootstrap):
            medias.append(sum(rng.choice(valores) for _ in valores) / len(valores))
        medias.sort()
        comparacao["bootstrap_ci95_low"] = medias[int(0.025 * bootstrap)]
        comparacao["bootstrap_ci95_high"] = medias[min(bootstrap - 1, int(0.975 * bootstrap))]
        comparacao["wilcoxon_holm"] = ajustados[i]

    destino = run / "analise_pareada_aceitacao.csv"
    campos = ["topology", "load_level", "algorithm", "n_scenarios",
              "mean_difference_pp", "median_difference_pp", "bootstrap_ci95_low",
              "bootstrap_ci95_high", "wilcoxon_p", "wilcoxon_holm", "rank_biserial"]
    with destino.open("w", encoding="utf-8", newline="") as fluxo:
        escritor = csv.DictWriter(fluxo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(comparacoes)
    return destino


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--bootstrap", type=int, default=10000)
    args = parser.parse_args(argv)
    print(analisar(args.run, bootstrap=args.bootstrap))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
