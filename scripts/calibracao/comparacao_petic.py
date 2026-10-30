"""Q-Learning contra o PETIC (e contra o caminho de custo mínimo), por alocação.

A cada chamada a allocate do Q-Learning, no mesmo estado do grafo e com o mesmo
previous_result, o PETIC (determinístico, não altera o grafo nem consome
números aleatórios) é consultado. Para cada alocação em que ambos acharam
caminho, registra-se se os caminhos são iguais e o custo exp(b/a) somado dos
enlaces de cada caminho. O custo não inclui a penalidade de troca de caminho
nem o bônus de reaproveitamento do PETIC: é o custo exp(b/a) puro, igual para
todos. O mínimo exato (Dijkstra com esse custo) é a terceira coluna de
referência, já que o PETIC pode divergir dele pelo reaproveitamento.

Uso: python3.11 -m scripts.calibracao.comparacao_petic GRADE.json SAIDA.csv
GRADE.json tem o mesmo formato das grades da varredura (só entradas q-learning).
"""
import csv
import heapq
import json
import math
import multiprocessing
from pathlib import Path
import sys

from scripts.calibracao.common import (
    LINK_CAPACITY, PROFILE, TOPOLOGIES, AlgorithmSpec, ExperimentRunner,
    allocator_parameters, build_requests, create_allocator, uniform_capacity,
)
from algorithms.petic.petic_allocator import PeticAllocator
from algorithms.petic.petic_weight_calculator import PeticWeightCalculator
from pathfinding.dijkstra_path_finder import DijkstraPathFinder

SCENARIO_SEED = 1001
RUN_SEEDS = range(1000, 1005)
SCENARIOS = (
    ("nobel-germany", 60, 3.0),
    ("nobel-germany", 80, 4.0),
    ("abilene", 80, 4.0),
)
FIELDS = [
    "label", "topology", "requests", "multiplier", "run_seed", "alocacoes",
    "ql_aceitas", "petic_aceitas", "ambas", "mesmo_caminho_petic",
    "mesmo_caminho_minimo", "excesso_custo_vs_petic", "excesso_custo_vs_minimo",
]


def edge_costs(graph, demand):
    costs = {}
    for link in graph.links:
        if not link.supports(demand.id, demand.bandwidth):
            continue
        key = frozenset((link.source.name, link.target.name))
        if key in costs:  # primeiro enlace do par, como NetworkGraph.get_link
            continue
        costs[key] = math.exp(
            demand.bandwidth / link.available_bandwidth_at(demand.id))
    return costs


def path_cost(path, costs):
    return sum(costs[frozenset(e)] for e in zip(path, path[1:]))


def min_cost(costs, source, destination):
    adjacency = {}
    for edge, cost in costs.items():
        a, b = tuple(edge)
        adjacency.setdefault(a, []).append((b, cost))
        adjacency.setdefault(b, []).append((a, cost))
    best = {source: 0.0}
    heap = [(0.0, source)]
    while heap:
        dist, node = heapq.heappop(heap)
        if node == destination:
            return dist
        if dist > best.get(node, math.inf):
            continue
        for nxt, cost in adjacency.get(node, ()):
            if dist + cost < best.get(nxt, math.inf):
                best[nxt] = dist + cost
                heapq.heappush(heap, (dist + cost, nxt))
    return None


class ComparingAllocator:
    def __init__(self, inner):
        self.inner = inner
        self.petic = PeticAllocator(DijkstraPathFinder(), PeticWeightCalculator())
        self.records = []

    def allocate(self, graph, request, demand, previous_result=None):
        result = self.inner.allocate(graph, request, demand, previous_result)
        ref = self.petic.allocate(graph, request, demand, previous_result)
        costs = edge_costs(graph, demand)
        source, destination = request.source.name, request.destination.name
        record = {"ql": result.accepted, "petic": ref.accepted}
        if result.accepted and ref.accepted:
            optimum = min_cost(costs, source, destination)
            ql_cost = path_cost(result.path, costs)
            petic_cost = path_cost(ref.path, costs)
            record.update(
                same_petic=result.path == ref.path,
                same_min=abs(ql_cost - optimum) < 1e-9,
                ql=ql_cost, petic_c=petic_cost, opt=optimum,
            )
        self.records.append(record)
        return result


def execute(job):
    label, parameters, (topology, n, mult), seed = job
    requests = build_requests(topology, n, mult, SCENARIO_SEED)
    holder = {}

    def factory(run_seed, service):
        inner = create_allocator("q-learning", service, run_seed, parameters=parameters)
        holder["a"] = ComparingAllocator(inner)
        return holder["a"]

    spec = AlgorithmSpec("q-learning", factory,
                         allocator_parameters("q-learning", parameters),
                         stochastic=True)
    ExperimentRunner().run(
        lambda: uniform_capacity(TOPOLOGIES[topology](), LINK_CAPACITY),
        requests, [spec], topology=topology, repetitions=1, seed=seed,
        period_order=tuple(PROFILE),
    )
    recs = holder["a"].records
    both = [r for r in recs if "same_petic" in r]
    ratio = lambda key, base: (
        sum(r[key] / r[base] - 1 for r in both) / len(both) if both else "")
    return {
        "label": label, "topology": topology, "requests": n, "multiplier": mult,
        "run_seed": seed, "alocacoes": len(recs),
        "ql_aceitas": sum(r["ql"] for r in recs),
        "petic_aceitas": sum(r["petic"] for r in recs), "ambas": len(both),
        "mesmo_caminho_petic": sum(r["same_petic"] for r in both),
        "mesmo_caminho_minimo": sum(r["same_min"] for r in both),
        "excesso_custo_vs_petic": ratio("ql", "petic_c"),
        "excesso_custo_vs_minimo": ratio("ql", "opt"),
    }


def main(grid_path, out):
    grid = json.loads(Path(grid_path).read_text(encoding="utf-8"))
    jobs = [(label, p, sc, s) for alg, label, p in grid if alg == "q-learning"
            for sc in SCENARIOS for s in RUN_SEEDS]
    with multiprocessing.get_context("fork").Pool(10) as pool, \
            open(out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, FIELDS)
        writer.writeheader()
        for row in pool.imap_unordered(execute, jobs):
            writer.writerow(row)
    print(f"{len(jobs)} execuções -> {out}")


if __name__ == "__main__":
    main(*sys.argv[1:])
