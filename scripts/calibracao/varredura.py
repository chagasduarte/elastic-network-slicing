"""Varredura de parâmetros de ACO e SA (qualidade e orçamento).

Higiene experimental: cenários com semente de cenário 1001 e sementes de
execução 1000..1004. A matriz final usa seed=42 (repetições 42+k) e os
cenários de experiments/configs/default.json, que NÃO são usados aqui (os
níveis de carga abaixo são próprios da calibração).

Os tempos desta varredura são medidos com processos em paralelo e servem só
como indicação; os tempos finais vêm de medicao_tempo.py (sequencial).

Uso: python3.11 -m scripts.calibracao.varredura ESTAGIO [--workers N]
Estágios: referencia, aco1, sa1, aco2, sa2, aco3, sa3
"""

import argparse
import csv
import itertools
import json
import multiprocessing
from pathlib import Path
import sys

from scripts.calibracao.common import build_requests, run_one

OUT = Path(__file__).resolve().parents[2] / "results" / "calibracao"
SCENARIO_SEED = 1001
RUN_SEEDS = range(1000, 1005)
# (topologia, requisições, multiplicador de carga): saturadas, mas distintas
# dos níveis de default.json.
SCENARIOS = (
    ("nobel-germany", 60, 3.0),
    ("nobel-germany", 80, 4.0),
    ("abilene", 80, 4.0),
)
FIELDS = [
    "stage", "algorithm", "label", "parameters", "topology", "requests",
    "multiplier", "scenario_seed", "run_seed", "acceptance_rate",
    "served_ratio", "max_utilization_percent", "jain_period_mean",
    "mean_hops", "mean_decision_ms_parallel", "construcoes", "avaliados",
    "expansoes", "buscas",
]


def sa_params(iterations, t0=0.25, tmin=0.001, **extra):
    """Resfriamento geométrico que atinge tmin em `iterations` passos."""
    cooling = round((tmin / t0) ** (1.0 / iterations), 6)
    return {
        "initial_temperature": t0, "minimum_temperature": tmin,
        "cooling_rate": cooling, "max_iterations": iterations, **extra,
    }


def jobs_for(stage):
    """Lista de (algoritmo, rótulo, parâmetros)."""
    if stage == "referencia":
        return [("petic", "petic", None), ("q-learning", "ql_default", None),
                ("aco", "aco_default", None), ("sa", "sa_default", None)]
    if stage == "aco1":  # orçamento: formigas x iterações
        return [("aco", f"a{a}_i{i}", {"ants_count": a, "iterations": i})
                for a, i in itertools.product((5, 10, 20, 40), (10, 20, 50, 100))]
    if stage == "sa1":  # orçamento: iterações x temperatura inicial
        out = [("sa", f"n{n}_T{t}", sa_params(n, t0=t))
               for n, t in itertools.product((50, 100, 200, 500, 1000, 2000),
                                             (0.25, 1.0))]
        return out
    if stage == "aco2":  # alpha, beta, evaporação, depósito em orçamento fixo
        base = {"ants_count": 20, "iterations": 20}
        return [("aco", f"al{al}_be{be}_ev{ev}_dep{dep}",
                 {**base, "alpha": al, "beta": be, "evaporation_rate": ev,
                  "pheromone_deposit": dep})
                for al, be, ev, dep in itertools.product(
                    (0.5, 1.0, 2.0), (1.0, 2.0, 4.0), (0.1, 0.3), (1.0, 5.0))]
    if stage == "sa2":  # Tmin, tentativas e passos de vizinho em N fixo
        out = []
        for n in (200,):
            for tmin, att, steps in itertools.product(
                    (0.001, 0.01), (10, 30, 60), (10, 20, 40)):
                out.append(("sa", f"n{n}_Tmin{tmin}_att{att}_st{steps}",
                            sa_params(n, tmin=tmin, neighbor_attempts=att,
                                      max_neighbor_steps=steps)))
        return out
    raise SystemExit(f"Estágio desconhecido: {stage}")


def execute(job):
    stage, algorithm, label, parameters, (topology, n, mult), run_seed = job
    requests = build_requests(topology, n, mult, SCENARIO_SEED)
    run, counters = run_one(topology, requests, algorithm, parameters, run_seed)
    s = run.summary
    return {
        "stage": stage, "algorithm": algorithm, "label": label,
        "parameters": json.dumps(parameters or {}, sort_keys=True),
        "topology": topology, "requests": n, "multiplier": mult,
        "scenario_seed": SCENARIO_SEED, "run_seed": run_seed,
        "acceptance_rate": s.acceptance.acceptance_rate,
        "served_ratio": s.bandwidth.served_ratio,
        "max_utilization_percent": s.network.max_utilization_percent,
        "jain_period_mean": s.network.fairness_jain_period_mean,
        "mean_hops": s.paths.mean_hops,
        "mean_decision_ms_parallel": s.timing.mean_seconds * 1000,
        "construcoes": counters.get("construcoes"),
        "avaliados": counters.get("avaliados"),
        "expansoes": counters.get("expansoes"),
        "buscas": counters.get("buscas"),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage")
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--extra-json", help="arquivo JSON com a lista de jobs (estágios aco3/sa3)")
    args = parser.parse_args()
    if args.extra_json:
        spec = json.loads(Path(args.extra_json).read_text(encoding="utf-8"))
        combos = [(a, l, p) for a, l, p in spec]
    else:
        combos = jobs_for(args.stage)
    jobs = [(args.stage, a, l, p, sc, rs) for a, l, p in combos
            for sc in SCENARIOS for rs in RUN_SEEDS]
    # Mais pesados primeiro, para equilibrar os processos.
    jobs.sort(key=lambda j: -(j[3] or {}).get("max_iterations", 0)
              - 20 * (j[3] or {}).get("iterations", 0) * (j[3] or {}).get("ants_count", 1) / 10)
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / f"varredura_{args.stage}.csv"
    with multiprocessing.get_context("fork").Pool(args.workers) as pool, target.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, FIELDS)
        writer.writeheader()
        for done, row in enumerate(pool.imap_unordered(execute, jobs), 1):
            writer.writerow(row)
            if done % 20 == 0:
                print(f"{done}/{len(jobs)}", file=sys.stderr, flush=True)
    print(f"{len(jobs)} execuções -> {target}")


if __name__ == "__main__":
    main()
