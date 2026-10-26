"""Fórmulas puras sobre medições, com desvio-padrão populacional."""

from copy import deepcopy
from statistics import fmean, pstdev

from metrics.collector import MetricsCollector
from metrics.models import (
    AcceptanceMetrics,
    AlgorithmCounters,
    BandwidthMetrics,
    DemandMeasurement,
    ExperimentMetadata,
    ExperimentMetrics,
    MetricSummary,
    NetworkMetrics,
    NetworkSnapshot,
    PathChangeMetrics,
    PathMetrics,
    PeriodMetrics,
    TimingMetrics,
)


def _ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def _mean(values: list[float]) -> float:
    return fmean(values) if values else 0.0


def _stddev(values: list[float]) -> float:
    return pstdev(values) if values else 0.0


class MetricsCalculator:
    def calculate(
        self, collector: MetricsCollector, metadata: ExperimentMetadata,
    ) -> ExperimentMetrics:
        measurements = collector.measurements
        snapshots = collector.network_snapshots
        if tuple(snapshot.period for snapshot in snapshots) != collector.period_order:
            raise ValueError("Capture a rede em todos os períodos antes de calcular métricas.")

        transitions = self._transitions(measurements, collector.period_order)
        periods = tuple(
            PeriodMetrics(
                period=period,
                metrics=self._summarize(
                    tuple(item for item in measurements if item.period == period),
                    (snapshots[index],),
                    transitions.get(period, []),
                ),
            )
            for index, period in enumerate(collector.period_order)
        )
        return ExperimentMetrics(
            metadata=deepcopy(metadata),
            summary=self._summarize(
                measurements, snapshots,
                [same for items in transitions.values() for same in items],
            ),
            periods=periods,
            measurements=measurements,
            network_snapshots=snapshots,
            period_order=collector.period_order,
        )

    def _summarize(
        self,
        measurements: tuple[DemandMeasurement, ...],
        snapshots: tuple[NetworkSnapshot, ...],
        transitions: list[bool],
    ) -> MetricSummary:
        processed = len(measurements)
        accepted = sum(item.accepted for item in measurements)
        acceptance = _ratio(accepted, processed)
        requested = sum(item.requested_bandwidth for item in measurements)
        allocated = sum(item.allocated_bandwidth for item in measurements)
        served = _ratio(allocated, requested)
        hops = [
            len(item.path) - 1
            for item in measurements if item.accepted and item.path_valid
        ]
        times = [item.elapsed_seconds for item in measurements]
        reused = sum(transitions)
        changed = len(transitions) - reused
        return MetricSummary(
            acceptance=AcceptanceMetrics(
                processed, accepted, processed - accepted, acceptance, 100 * acceptance,
            ),
            bandwidth=BandwidthMetrics(
                requested, allocated, requested - allocated, served, 100 * served,
            ),
            network=self._network(snapshots),
            paths=PathMetrics(
                len(hops), _mean(hops), min(hops, default=0), max(hops, default=0), sum(hops),
            ),
            timing=TimingMetrics(
                sum(times), _mean(times), min(times, default=0.0),
                max(times, default=0.0), _stddev(times),
            ),
            path_changes=PathChangeMetrics(
                len(transitions), reused, changed,
                _ratio(reused, len(transitions)), _ratio(changed, len(transitions)),
            ),
            counters=self._counters(measurements),
        )

    @staticmethod
    def _network(snapshots: tuple[NetworkSnapshot, ...]) -> NetworkMetrics:
        links = [link for snapshot in snapshots for link in snapshot.links]
        physical = {}
        for link in links:
            key = (link.source, link.target)
            if key in physical and physical[key] != link.capacity:
                raise ValueError("A capacidade física mudou entre períodos do experimento.")
            physical[key] = link.capacity
        utilizations = [link.utilization for link in links]
        capacity = sum(link.capacity for link in links)
        used = sum(link.used_bandwidth for link in links)
        saturated = [link for link in links if link.used_bandwidth >= link.capacity]
        # Todos os enlaces entram, inclusive ociosos; nenhuma carga => Jain 0.
        fairness = _ratio(
            sum(utilizations) ** 2,
            len(utilizations) * sum(value ** 2 for value in utilizations),
        )
        return NetworkMetrics(
            physical_capacity=sum(physical.values()),
            total_capacity=capacity,
            total_used_bandwidth=used,
            residual_capacity=capacity - used,
            link_count=len(physical),
            link_period_count=len(links),
            average_utilization_percent=100 * _mean(utilizations),
            weighted_utilization_percent=100 * _ratio(used, capacity),
            max_utilization_percent=100 * max(utilizations, default=0.0),
            saturated_links=len({(link.source, link.target) for link in saturated}),
            saturated_link_periods=len(saturated),
            fairness_jain=fairness,
            utilization_stddev=_stddev(utilizations),
        )

    @staticmethod
    def _transitions(
        measurements: tuple[DemandMeasurement, ...], period_order: tuple[str, ...],
    ) -> dict[str, list[bool]]:
        records = {(item.request_id, item.period): item for item in measurements}
        period_index = {period: index for index, period in enumerate(period_order)}
        transitions: dict[str, list[bool]] = {}
        for item in measurements:
            index = period_index[item.period]
            if not index or not item.accepted or not item.path_valid:
                continue
            previous = records.get((item.request_id, period_order[index - 1]))
            if previous is not None and previous.accepted and previous.path_valid:
                transitions.setdefault(item.period, []).append(previous.path == item.path)
        return transitions

    @staticmethod
    def _counters(measurements: tuple[DemandMeasurement, ...]) -> AlgorithmCounters:
        def total(values: list[int | None]) -> int | None:
            return sum(values) if values and all(value is not None for value in values) else None

        names = ("path_search_attempts", "paths_evaluated", "iterations", "nodes_visited")
        extra_keys = {key for item in measurements for key in item.counters.extra}
        return AlgorithmCounters(
            **{
                name: total([getattr(item.counters, name) for item in measurements])
                for name in names
            },
            extra={
                key: total([item.counters.extra.get(key) for item in measurements])
                for key in sorted(extra_keys)
            },
        )
