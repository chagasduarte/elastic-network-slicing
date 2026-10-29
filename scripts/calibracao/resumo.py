"""Resume um CSV de varredura: média por configuração (sobre cenários e sementes).

Uso: python3.11 -m scripts.calibracao.resumo ESTAGIO [ESTAGIO ...]
Grava results/calibracao/resumo_<estagio>.csv e imprime a tabela.
"""
import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev
import sys

OUT = Path(__file__).resolve().parents[2] / "results" / "calibracao"
METRICS = ["acceptance_rate", "served_ratio", "max_utilization_percent",
           "jain_period_mean", "mean_hops", "mean_decision_ms_parallel",
           "construcoes", "avaliados", "expansoes"]


def load(stage):
    with (OUT / f"varredura_{stage}.csv").open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def summarize(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[(r["algorithm"], r["label"])].append(r)
    table = []
    for (alg, label), rs in groups.items():
        row = {"algorithm": alg, "label": label, "n": len(rs)}
        for m in METRICS:
            vals = [float(r[m]) for r in rs if r[m] not in ("", None)]
            row[m] = mean(vals) if vals else None
        # Erro-padrão da taxa de banda atendida entre execuções.
        vals = [float(r["served_ratio"]) for r in rs]
        row["served_se"] = stdev(vals) / len(vals) ** 0.5 if len(vals) > 1 else None
        table.append(row)
    return table


def main():
    for stage in sys.argv[1:]:
        table = summarize(load(stage))
        fields = ["algorithm", "label", "n"] + METRICS + ["served_se"]
        with (OUT / f"resumo_{stage}.csv").open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fields)
            w.writeheader()
            for row in table:
                w.writerow({k: (f"{v:.5g}" if isinstance(v, float) else v)
                            for k, v in row.items()})
        print(f"== {stage}")
        print("label".ljust(34), "acc", "served", "maxU", "jain", "hops", "ms*", "constr", "aval", "expans")
        for r in table:
            f = lambda k, p=3: "-" if r[k] is None else f"{r[k]:.{p}f}"
            print(r["label"].ljust(34), f("acceptance_rate"), f("served_ratio", 4),
                  f("max_utilization_percent", 1), f("jain_period_mean", 4),
                  f("mean_hops", 3), f("mean_decision_ms_parallel", 1),
                  f("construcoes", 0), f("avaliados", 0), f("expansoes", 0))


if __name__ == "__main__":
    main()
