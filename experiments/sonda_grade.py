"""Sonda da grade de cargas usando só o PETIC (rápido e determinístico).

Uso: python3.11 -m experiments.sonda_grade --config experiments/configs/default.json

Para cada topologia e nível imprime aceitação e utilização (máxima/média, em %)
e enlaces >= 90% por período. É diagnóstico da grade, não calibração: usa a
semente de cenário da config e uma única repetição.
"""

import argparse
from pathlib import Path

from experiments.cli import TOPOLOGIES, create_algorithm_specs, executar_celula
from experiments.scenarios import load_config


def sondar(config, topologias=None):
    specs = create_algorithm_specs(("petic",))
    for topologia in topologias or config.topologies:
        pares = len(TOPOLOGIES[topologia]().nodes)
        pares *= pares - 1
        for nivel in config.load_levels:
            if nivel.requests > pares:
                print(f"{topologia:<14}{nivel.name:<4} pulado: {nivel.requests} requisições "
                      f"excedem os {pares} pares")
                continue
            runs, _ = executar_celula(topologia, nivel, config, specs,
                                      repetitions=1, seed=config.seed)
            run = runs[0]
            periodos = " ".join(
                f"{p.period}:{p.metrics.acceptance.acceptance_percent:.0f}%"
                f"/max{p.metrics.network.max_utilization_percent:.0f}"
                f"/med{p.metrics.network.average_utilization_percent:.0f}"
                f"/s90={p.metrics.network.saturated_links_90}"
                for p in run.periods
            )
            print(f"{topologia:<14}{nivel.name:<4}{nivel.requests:>4} x{nivel.multiplier:<4} "
                  f"acc={run.summary.acceptance.acceptance_percent:6.1f} "
                  f"serv={run.summary.bandwidth.served_percent:6.1f} | {periodos}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path,
                        default=Path("experiments/configs/default.json"))
    parser.add_argument("--topologies", nargs="+", choices=TOPOLOGIES)
    args = parser.parse_args(argv)
    sondar(load_config(args.config), args.topologies)


if __name__ == "__main__":
    main()
