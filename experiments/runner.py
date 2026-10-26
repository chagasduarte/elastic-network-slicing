"""Orquestra alocação, reserva e coleta sem acoplar métricas a algoritmos."""

from collections.abc import Callable, Sequence
from copy import deepcopy
from dataclasses import asdict, dataclass, field
import hashlib
import heapq
import json
import time
from typing import Any

from contracts.slice_allocator import SliceAllocator
from domain.link_allocation import LinkAllocation
from domain.network_graph import NetworkGraph
from domain.slice_request import SliceRequest
from domain.slice_result import SliceResult
from metrics.calculator import MetricsCalculator
from metrics.collector import MetricsCollector
from metrics.models import ExperimentMetadata, ExperimentMetrics
from services.bandwidth_reservation_service import BandwidthReservationService


@dataclass(frozen=True)
class AlgorithmSpec:
    name: str
    factory: Callable[[int | None, BandwidthReservationService], SliceAllocator]
    parameters: dict[str, Any] = field(default_factory=dict)
    stochastic: bool = True


class ExperimentRunner:
    """Cada repetição usa cópias novas de grafo, requisições e alocador.

    A ordem das requisições é fixa e compartilhada pelos algoritmos. A ordem
    dos algoritmos é rotacionada entre repetições. Tempos cobrem somente
    allocate; reservas, snapshots, criação dos objetos e exportação ficam fora.
    """

    def run(
        self,
        topology_factory: Callable[[], NetworkGraph],
        requests: Sequence[SliceRequest],
        algorithms: Sequence[AlgorithmSpec],
        *,
        topology: str = "custom",
        scenario_id: str | None = None,
        repetitions: int = 5,
        seed: int = 42,
        period_order: Sequence[str] | None = None,
    ) -> list[ExperimentMetrics]:
        if type(repetitions) is not int or repetitions < 1:
            raise ValueError("repetitions deve ser um inteiro positivo.")
        if type(seed) is not int:
            raise ValueError("seed deve ser um inteiro.")
        specs = tuple(algorithms)
        if not specs or any(not spec.name for spec in specs):
            raise ValueError("Informe ao menos um algoritmo com nome.")
        if len({spec.name for spec in specs}) != len(specs):
            raise ValueError("Os nomes dos algoritmos devem ser únicos.")

        template_requests = deepcopy(tuple(requests))
        self._validate_requests(template_requests)
        periods = self._periods(template_requests, period_order)
        expected_topology = None
        results = []

        for repetition in range(repetitions):
            offset = repetition % len(specs)
            for spec in specs[offset:] + specs[:offset]:
                # deepcopy também protege factories que retornam um grafo cacheado.
                graph = deepcopy(topology_factory())
                signature = self._topology_signature(graph)
                if expected_topology is None:
                    expected_topology = signature
                    if scenario_id is None:
                        scenario_id = self._scenario_id(
                            signature, template_requests, periods
                        )
                elif signature != expected_topology:
                    raise ValueError(
                        "A fábrica alterou a topologia ou a ordem dos enlaces "
                        "entre execuções."
                    )
                run_requests = deepcopy(template_requests)
                self._validate_endpoints(graph, run_requests)
                service = BandwidthReservationService()
                run_seed = seed + repetition if spec.stochastic else None
                allocator = spec.factory(run_seed, service)
                collector = MetricsCollector(periods)
                previous: dict[str, tuple[int, SliceResult]] = {}

                for period_index, period in enumerate(periods):
                    for request in run_requests:
                        demand = next(
                            (item for item in request.demands if item.id == period),
                            None,
                        )
                        if demand is None:
                            continue
                        last = previous.get(request.id)
                        previous_result = (
                            last[1] if last is not None
                            and last[0] == period_index - 1 else None
                        )
                        started = time.perf_counter()
                        result = allocator.allocate(
                            graph, request, demand, previous_result
                        )
                        elapsed = time.perf_counter() - started
                        self._validate_result(graph, request, demand, result)
                        if result.accepted:
                            service.reserve(
                                graph.get_links_from_path(result.path),
                                LinkAllocation(
                                    result.request_id,
                                    result.demand_id,
                                    result.bandwidth,
                                ),
                            )
                        collector.record(graph, request, demand, result, elapsed)
                        previous[request.id] = (period_index, result)
                    collector.snapshot_period(graph, period)

                metadata = ExperimentMetadata(
                    algorithm=spec.name,
                    topology=topology,
                    run_id=f"{scenario_id}:{spec.name}:{repetition + 1}",
                    seed=run_seed,
                    parameters=deepcopy(spec.parameters),
                    scenario_id=scenario_id,
                )
                results.append(MetricsCalculator().calculate(collector, metadata))
        return results

    @staticmethod
    def _validate_requests(requests: Sequence[SliceRequest]) -> None:
        ids = [request.id for request in requests]
        if any(not request_id for request_id in ids) or len(set(ids)) != len(ids):
            raise ValueError("Os IDs das requisições devem ser únicos e não vazios.")
        for request in requests:
            periods = [demand.id for demand in request.demands]
            if len(set(periods)) != len(periods):
                raise ValueError(
                    f"A requisição {request.id} repete um identificador de período."
                )

    @staticmethod
    def _periods(
        requests: Sequence[SliceRequest], explicit: Sequence[str] | None
    ) -> tuple[str, ...]:
        # Não ordena lexicograficamente: t10 pode vir depois de t9 e IDs são livres.
        first_seen = dict.fromkeys(
            demand.id for request in requests for demand in request.demands
        )
        if explicit is not None:
            periods = tuple(explicit)
            if any(not period for period in periods) or len(set(periods)) != len(periods):
                raise ValueError("period_order deve conter IDs únicos e não vazios.")
            positions = {period: index for index, period in enumerate(periods)}
            if not set(first_seen).issubset(positions):
                raise ValueError("period_order não contém todos os períodos das demandas.")
            for request in requests:
                indices = [positions[demand.id] for demand in request.demands]
                if indices != sorted(indices):
                    raise ValueError("period_order contradiz a ordem de request.demands.")
            return periods

        ranks = {period: index for index, period in enumerate(first_seen)}
        successors = {period: set() for period in first_seen}
        indegree = dict.fromkeys(first_seen, 0)
        for request in requests:
            for before, after in zip(request.demands, request.demands[1:]):
                if after.id not in successors[before.id]:
                    successors[before.id].add(after.id)
                    indegree[after.id] += 1
        pending = [ranks[period] for period in first_seen if indegree[period] == 0]
        heapq.heapify(pending)
        names = tuple(first_seen)
        ordered = []
        while pending:
            period = names[heapq.heappop(pending)]
            ordered.append(period)
            for successor in successors[period]:
                indegree[successor] -= 1
                if indegree[successor] == 0:
                    heapq.heappush(pending, ranks[successor])
        if len(ordered) != len(first_seen):
            raise ValueError("As requisições têm ordens de períodos incompatíveis.")
        return tuple(ordered)

    @staticmethod
    def _topology_signature(graph: NetworkGraph) -> tuple:
        if any(link.allocations for link in graph.links):
            raise ValueError("Cada execução deve começar sem reservas nos enlaces.")
        return (
            tuple(sorted(node.name for node in graph.nodes)),
            tuple(
                (link.source.name, link.target.name, link.capacity)
                for link in graph.links
            ),
        )

    @staticmethod
    def _validate_endpoints(graph: NetworkGraph, requests: Sequence[SliceRequest]) -> None:
        for request in requests:
            if any(graph.get_node(node.name) is None
                   for node in (request.source, request.destination)):
                raise ValueError(f"A requisição {request.id} usa um nó inexistente.")

    @staticmethod
    def _validate_result(graph, request, demand, result) -> None:
        if not isinstance(result, SliceResult):
            raise ValueError("O alocador deve retornar SliceResult.")
        if result.request_id != request.id or result.demand_id != demand.id:
            raise ValueError("O resultado não corresponde à requisição/período atual.")
        if not result.accepted:
            if result.path:
                raise ValueError("Um resultado rejeitado não deve conter caminho.")
            return
        if (
            not result.path
            or result.path[0] != request.source.name
            or result.path[-1] != request.destination.name
            or len(set(result.path)) != len(result.path)
            or result.bandwidth != demand.bandwidth
        ):
            raise ValueError("O resultado aceito contém caminho ou banda inválidos.")
        links = graph.get_links_from_path(result.path)
        if any(not link.supports(demand.id, result.bandwidth) for link in links):
            raise ValueError("O caminho aceito não possui capacidade disponível.")

    @staticmethod
    def _scenario_id(signature, requests, periods) -> str:
        blueprint = {
            "topology": signature,
            "requests": [asdict(request) for request in requests],
            "period_order": periods,
        }
        encoded = json.dumps(blueprint, sort_keys=True, ensure_ascii=False).encode()
        return hashlib.sha256(encoded).hexdigest()[:16]
