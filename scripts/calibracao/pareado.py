"""Diferença pareada de cada configuração contra uma base, mesmo cenário e semente.

As configurações compartilham cenário e semente de execução, então a diferença
pareada tem muito menos ruído que a comparação entre médias.
Uso: python3.11 -m scripts.calibracao.pareado ESTAGIO ROTULO_BASE [ESTAGIO_BASE]
Grava results/calibracao/pareado_<estagio>.csv e imprime a tabela.
"""
import csv
from collections import defaultdict
from statistics import mean, stdev
import sys

from scripts.calibracao.resumo import OUT, load

METRICS = ["served_ratio", "acceptance_rate", "max_utilization_percent",
           "jain_period_mean", "mean_hops"]


def key(r):
    return (r["topology"], r["requests"], r["multiplier"], r["run_seed"])


def main(stage, base_label, base_stage=None):
    base_rows = [r for r in load(base_stage or stage) if r["label"] == base_label]
    base = {key(r): r for r in base_rows}
    groups = defaultdict(list)
    for r in load(stage):
        if key(r) in base:
            groups[(r["algorithm"], r["label"])].append(r)
    fields = ["algorithm", "label", "n", "base"]
    for m in METRICS:
        fields += [f"d_{m}", f"se_{m}"]
    fields.append("mean_decision_ms_parallel")
    rows = []
    for (alg, label), rs in groups.items():
        row = {"algorithm": alg, "label": label, "n": len(rs), "base": base_label}
        for m in METRICS:
            d = [float(r[m]) - float(base[key(r)][m]) for r in rs]
            row[f"d_{m}"] = round(mean(d), 5)
            row[f"se_{m}"] = round(stdev(d) / len(d) ** 0.5, 5) if len(d) > 1 else ""
        row["mean_decision_ms_parallel"] = round(
            mean(float(r["mean_decision_ms_parallel"]) for r in rs), 2)
        rows.append(row)
    rows.sort(key=lambda r: -r["d_served_ratio"])
    with (OUT / f"pareado_{stage}.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fields)
        w.writeheader()
        w.writerows(rows)
    print("label".ljust(34), "n  d_served(se)  d_jain  d_hops  d_maxU  ms*")
    for r in rows:
        print(r["label"].ljust(34), r["n"], f"{r['d_served_ratio']:+.4f}({r['se_served_ratio']})",
              f"{r['d_jain_period_mean']:+.4f}", f"{r['d_mean_hops']:+.3f}",
              f"{r['d_max_utilization_percent']:+.2f}", r["mean_decision_ms_parallel"])


if __name__ == "__main__":
    main(*sys.argv[1:])
