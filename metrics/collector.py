"""Coleta após a reserva; não escolhe caminhos nem modifica o grafo."""

import math
from collections.abc import Sequence
from copy import deepcopy

from domain.network_graph import NetworkGraph
from domain.slice_demand import SliceDemand
from domain.slice_request import SliceRequest
from domain.slice_result import SliceResult
from metrics.models import (
    AlgorithmCounters,
    DemandMeasurement,
    LinkMeasurement,
    NetworkSnapshot,
)


class MetricsCollector:
    def __init__(self, period_order: Sequence[str]):
        self.period_order = tuple(period_order)
        if any(not period for period in self.period_order):
            raise ValueError("Os períodos devem possuir identificadores.")
        if len(set(self.period_order)) != len(self.period_order):
            raise ValueError("A ordem de períodos não pode conter duplicatas.")
        self._measurements: list[DemandMeasurement] = []
        self._keys: set[tuple[str, str]] = set()
        self._snapshots: dict[str, NetworkSnapshot] = {}

    @property
    def measurements(self) -> tuple[DemandMeasurement, ...]:
        return tuple(deepcopy(self._measurements))

    @property
    def network_snapshots(self) -> tuple[NetworkSnapshot, ...]:
        return tuple(
            self._snapshots[period]
            for period in self.period_order
            if period in self._snapshots
        )

    def record(
        self,
        graph: NetworkGraph,
        request: SliceRequest,
        demand: SliceDemand,
        result: SliceResult,
        elapsed_seconds: float,
        counters: AlgorithmCounters | None = None,
    ) -> None:
        """Registra banda efetivamente reservada, sem contar uma vez por salto.

        Caminhos inválidos não contribuem para banda atendida ou saltos. Para
        origem=destino, um caminho unitário válido atende a banda sem enlaces.
        """
        self._check_period(demand.id)
        if (result.request_id, result.demand_id) != (request.id, demand.id):
            raise ValueError("O resultado não corresponde à requisição/demanda.")
        if not math.isfinite(elapsed_seconds) or elapsed_seconds < 0:
            raise ValueError("O tempo deve ser finito e não negativo.")
        if demand not in request.demands:
            raise ValueError("A demanda não pertence à requisição.")
        key = (request.id, demand.id)
        if key in self._keys:
            raise ValueError("A demanda desta requisição já foi registrada.")

        path = tuple(result.path)
        valid = bool(
            path
            and path[0] == request.source.name
            and path[-1] == request.destination.name
            and len(path) == len(set(path))
            and all(graph.get_node(name) is not None for name in path)
            and all(
                graph.get_link(source, target) is not None
                for source, target in zip(path, path[1:])
            )
        )
        allocated = 0.0
        if result.accepted and valid:
            if len(path) == 1:
                allocated = float(result.bandwidth)
            else:
                allocated = min(
                    sum(
                        allocation.bandwidth
                        for allocation in link.allocations
                        if allocation.request_id == request.id
                        and allocation.demand_id == demand.id
                    )
                    for link in graph.get_links_from_path(list(path))
                )
            if not 0 <= allocated <= demand.bandwidth:
                raise ValueError("A banda reservada excede a banda solicitada.")

        self._measurements.append(DemandMeasurement(
            request_id=request.id,
            period=demand.id,
            source=request.source.name,
            destination=request.destination.name,
            requested_bandwidth=demand.bandwidth,
            allocated_bandwidth=allocated,
            accepted=result.accepted,
            path=path,
            path_valid=valid,
            elapsed_seconds=elapsed_seconds,
            counters=deepcopy(counters) if counters is not None else AlgorithmCounters(),
        ))
        self._keys.add(key)

    def snapshot_period(self, graph: NetworkGraph, period_id: str) -> None:
        """Captura o estado final do período, incluindo enlaces ociosos.

        O domínio identifica enlaces por extremos não ordenados. Espelhos com
        a mesma capacidade e reservas equivalentes contam uma vez. Também é
        aceita uma vista espelhada vazia; duas vistas preenchidas e diferentes
        são ambíguas e causam erro, sem presumir circuitos paralelos.
        """
        self._check_period(period_id)
        unique: dict[tuple[str, str], tuple[float, dict[tuple[str, str], float]]] = {}
        for link in graph.links:
            key = tuple(sorted((link.source.name, link.target.name)))
            allocations: dict[tuple[str, str], float] = {}
            for allocation in link.allocations:
                allocation_key = (allocation.request_id, allocation.demand_id)
                allocations[allocation_key] = (
                    allocations.get(allocation_key, 0) + allocation.bandwidth
                )
            if key in unique:
                capacity, previous = unique[key]
                if capacity != link.capacity:
                    raise ValueError(f"Enlaces espelhados com capacidades diferentes: {key}.")
                if previous and allocations and previous != allocations:
                    raise ValueError(f"Enlaces espelhados com reservas conflitantes: {key}.")
                allocations = previous or allocations
            unique[key] = (link.capacity, allocations)

        links = []
        for (source, target), (capacity, allocations) in unique.items():
            used = sum(
                bandwidth
                for (_, period), bandwidth in allocations.items()
                if period == period_id
            )
            if used > capacity:
                raise ValueError(f"Reservas excedem a capacidade de {source}-{target}.")
            links.append(LinkMeasurement(source, target, capacity, used))
        self._snapshots[period_id] = NetworkSnapshot(period_id, tuple(links))

    def _check_period(self, period: str) -> None:
        if period not in self.period_order:
            raise ValueError(f"Período ausente da ordem do experimento: {period}.")
