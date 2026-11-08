"""Comparação dos alocadores: python -m experiments.cli --help."""

import argparse
from functools import partial
import json
from pathlib import Path

from contracts.abilene_topology import create_abilene_graph
from contracts.create_topo import create_test_graph
from contracts.geant_topology import create_geant_graph
from contracts.germany50_topology import create_germany50_graph
from contracts.nobel_germany_topology import create_nobel_germany_graph
from domain.node import Node
from domain.slice_demand import SliceDemand
from domain.slice_request import SliceRequest
from experiments.runner import AlgorithmSpec, ExperimentRunner
from main import allocator_parameters, create_allocator
from metrics.aggregation import aggregate_runs
from experiments.scenarios import generate_requests, load_config, uniform_capacity
from metrics.exporter import MetricsExporter


TOPOLOGIES = {
    "test": create_test_graph,
    "abilene": create_abilene_graph,
    "nobel-germany": create_nobel_germany_graph,
    "geant": create_geant_graph,
    "germany50": create_germany50_graph,
}
ALGORITHMS = ("petic", "aco", "sa", "q-learning")


def _allocator_factory(seed, reservation_service, *, algorithm, parameters):
    return create_allocator(
        algorithm, reservation_service, seed, parameters=parameters
    )


def create_algorithm_specs(names=ALGORITHMS, parameter_overrides=None):
    """Metadados e factory compartilham a mesma configuração efetiva."""
    overrides = {} if parameter_overrides is None else parameter_overrides
    unknown = set(overrides) - set(names)
    if unknown:
        raise ValueError(f"Parâmetros para algoritmos não selecionados: {sorted(unknown)}")
    specs = []
    for name in names:
        parameters = allocator_parameters(name, overrides.get(name))
        specs.append(AlgorithmSpec(
            name=name,
            factory=partial(
                _allocator_factory,
                algorithm=name,
                parameters={} if name == "petic" else parameters,
            ),
            parameters=parameters,
            stochastic=name != "petic",
        ))
    return specs


def executar_celula(topology, level, config, specs, *, repetitions, seed):
    """Roda uma célula (topologia, nível de carga) com todos os algoritmos.

    Compartilhada por `--config` e por `experiments.run_all`; devolve
    (execuções, agregados).
    """
    def factory():
        return uniform_capacity(TOPOLOGIES[topology](), config.link_capacity)

    requests = generate_requests(
        factory(), level, config.profile,
        base_bandwidth=config.base_bandwidth,
        noise=config.noise, seed=seed,
    )
    runs = ExperimentRunner().run(
        factory, requests, specs, topology=topology,
        repetitions=repetitions, seed=seed,
        period_order=tuple(config.profile.factors),
    )
    return runs, aggregate_runs(runs)


def _run_config(parser, args) -> None:
    try:
        config = load_config(args.config)
        topologies = [args.topology] if args.topology else config.topologies
        unknown = [name for name in topologies if name not in TOPOLOGIES]
        if unknown:
            raise ValueError(f"Topologias desconhecidas: {unknown}")
        names = tuple(args.algorithms or config.algorithms)
        repetitions = args.repetitions or config.repetitions
        seed = config.seed if args.seed is None else args.seed
        specs = create_algorithm_specs(names, {
            name: values for name, values in config.parameters.items()
            if name in names
        })
        exporter = MetricsExporter()
        for topology in topologies:
            for level in config.load_levels:
                runs, aggregates = executar_celula(
                    topology, level, config, specs,
                    repetitions=repetitions, seed=seed,
                )
                target = args.output / topology / level.name
                exporter.export_json(runs, target / "runs.json", aggregates=aggregates)
                exporter.export_csv(runs, target / "runs.csv")
                exporter.export_aggregates_csv(aggregates, target / "aggregates.csv")
                print(f"\n=== {topology} | carga {level.name} "
                      f"({level.requests} requisições, x{level.multiplier}) ===")
                print(exporter.format_terminal(runs, aggregates=aggregates))
    except (ValueError, TypeError, OSError, KeyError) as error:
        parser.error(str(error))
    print(f"Resultados: {args.output.resolve()}")


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(
        description="Compara alocadores em cenários idênticos com reservas isoladas."
    )
    parser.add_argument(
        "--config", type=Path,
        help="JSON de cenários (experiments/configs/); gera várias requisições "
             "por nível de carga. --topology, --algorithms, --repetitions e "
             "--seed, se informados, substituem os valores do arquivo.",
    )
    parser.add_argument("--topology", choices=TOPOLOGIES)
    parser.add_argument("--algorithms", choices=ALGORITHMS, nargs="+")
    parser.add_argument("--repetitions", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--source", default="A")
    parser.add_argument("--destination", default="L")
    parser.add_argument(
        "--bandwidths", type=int, nargs="+", default=[40, 50, 15, 320],
        help="Demandas nos períodos t1, t2, ... (Mbps).",
    )
    parser.add_argument(
        "--parameters", type=Path,
        help='JSON de ajustes por algoritmo, ex.: {"q-learning": {"episodes": 100}}.',
    )
    parser.add_argument("--output", type=Path, default=Path("results/experiment"))
    args = parser.parse_args(argv)

    if args.config is not None:
        _run_config(parser, args)
        return
    args.topology = args.topology or "test"
    args.algorithms = args.algorithms or ALGORITHMS
    args.repetitions = 5 if args.repetitions is None else args.repetitions
    args.seed = 42 if args.seed is None else args.seed

    try:
        overrides = (
            json.loads(args.parameters.read_text(encoding="utf-8"))
            if args.parameters is not None else {}
        )
        if not isinstance(overrides, dict) or any(
            not isinstance(value, dict) for value in overrides.values()
        ):
            raise ValueError("--parameters deve conter objetos por nome de algoritmo.")
        specs = create_algorithm_specs(args.algorithms, overrides)
        requests = [SliceRequest(
            "request-1", Node(args.source), Node(args.destination),
            [SliceDemand(f"t{index}", bandwidth)
             for index, bandwidth in enumerate(args.bandwidths, start=1)],
        )]
        runs = ExperimentRunner().run(
            TOPOLOGIES[args.topology], requests, specs,
            topology=args.topology, repetitions=args.repetitions, seed=args.seed,
        )
    except (ValueError, TypeError, OSError) as error:
        parser.error(str(error))

    aggregates = aggregate_runs(runs)
    exporter = MetricsExporter()
    exporter.export_json(runs, args.output / "runs.json", aggregates=aggregates)
    exporter.export_csv(runs, args.output / "runs.csv")
    exporter.export_aggregates_csv(aggregates, args.output / "aggregates.csv")
    print(exporter.format_terminal(runs, aggregates=aggregates))
    print(f"Resultados: {args.output.resolve()}")


if __name__ == "__main__":
    main()
