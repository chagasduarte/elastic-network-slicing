"""Tempo de decisão SEQUENCIAL (sem paralelismo, sem contadores).

Mede a média e a mediana do tempo por chamada a allocate (apenas allocate,
como o runner) para configurações listadas em JSON:
[["aco","rotulo",{parametros}], ...]; `null` usa os defaults do código.
Uso: python3.11 -m scripts.calibracao.medicao_tempo CONFIGS.json SAIDA.csv
"""
import csv
import json
from statistics import mean, median
import sys

from scripts.calibracao.common import build_requests, run_one

SCENARIOS = (("nobel-germany", 60, 3.0), ("abilene", 80, 4.0))
SEEDS = (1000, 1001, 1002)
SCENARIO_SEED = 1001


def main(config_path, out):
    configs = json.load(open(config_path, encoding="utf-8"))
    rows = []
    for algorithm, label, parameters in configs:
        times = []
        for topology, n, mult in SCENARIOS:
            requests = build_requests(topology, n, mult, SCENARIO_SEED)
            for seed in SEEDS:
                run, _ = run_one(topology, requests, algorithm, parameters,
                                 seed, count=False)
                times += [m.elapsed_seconds * 1000 for m in run.measurements
                          if m.path_valid or not m.accepted]
        times.sort()
        rows.append({
            "algorithm": algorithm, "label": label,
            "parameters": json.dumps(parameters or {}, sort_keys=True),
            "allocations": len(times),
            "mean_ms": round(mean(times), 3),
            "median_ms": round(median(times), 3),
            "p95_ms": round(times[int(0.95 * (len(times) - 1))], 3),
        })
        print(rows[-1], flush=True)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
