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


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(
        description="Compara alocadores em cenários idênticos com reservas isoladas."
    )
    parser.add_argument("--topology", choices=TOPOLOGIES, default="test")
    parser.add_argument("--algorithms", choices=ALGORITHMS, nargs="+", default=ALGORITHMS)
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
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
