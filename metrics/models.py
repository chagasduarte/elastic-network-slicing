"""Objetos de métricas independentes das implementações dos alocadores."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AlgorithmCounters:
    """None indica informação não instrumentada, nunca esforço igual a zero."""

    path_search_attempts: int | None = None
    paths_evaluated: int | None = None
    iterations: int | None = None
    nodes_visited: int | None = None
    extra: dict[str, int | None] = field(default_factory=dict)


@dataclass(frozen=True)
class ExperimentMetadata:
    algorithm: str
    topology: str
    run_id: str
    seed: int | None
    parameters: dict[str, Any] = field(default_factory=dict)
    scenario_id: str = ""


@dataclass(frozen=True)
class DemandMeasurement:
    request_id: str
    period: str
    source: str
    destination: str
    requested_bandwidth: float
    allocated_bandwidth: float
    accepted: bool
    path: tuple[str, ...]
    path_valid: bool
    elapsed_seconds: float
    counters: AlgorithmCounters


@dataclass(frozen=True)
class LinkMeasurement:
    source: str
    target: str
    capacity: float
    used_bandwidth: float

    @property
    def utilization(self) -> float:
        return self.used_bandwidth / self.capacity


@dataclass(frozen=True)
class NetworkSnapshot:
    period: str
    links: tuple[LinkMeasurement, ...]


@dataclass(frozen=True)
class AcceptanceMetrics:
    processed: int
    accepted: int
    rejected: int
    acceptance_rate: float
    acceptance_percent: float


@dataclass(frozen=True)
class BandwidthMetrics:
    requested: float
    allocated: float
    rejected: float
    served_ratio: float
    served_percent: float


@dataclass(frozen=True)
class NetworkMetrics:
    # No resumo, total_capacity/used/residual somam observações enlace-período.
    # physical_capacity conta cada enlace uma vez, sem multiplicar por períodos.
    physical_capacity: float
    total_capacity: float
    total_used_bandwidth: float
    residual_capacity: float
    link_count: int
    link_period_count: int
    average_utilization_percent: float
    weighted_utilization_percent: float
    max_utilization_percent: float
    saturated_links: int
    saturated_link_periods: int
    fairness_jain: float
    utilization_stddev: float


@dataclass(frozen=True)
class PathMetrics:
    accepted_paths: int
    mean_hops: float
    min_hops: int
    max_hops: int
    total_hops: int


@dataclass(frozen=True)
class TimingMetrics:
    total_seconds: float
    mean_seconds: float
    min_seconds: float
    max_seconds: float
    stddev_seconds: float


@dataclass(frozen=True)
class PathChangeMetrics:
    comparable_transitions: int
    reused: int
    changed: int
    reuse_rate: float
    change_rate: float


@dataclass(frozen=True)
class MetricSummary:
    acceptance: AcceptanceMetrics
    bandwidth: BandwidthMetrics
    network: NetworkMetrics
    paths: PathMetrics
    timing: TimingMetrics
    path_changes: PathChangeMetrics
    counters: AlgorithmCounters


@dataclass(frozen=True)
class PeriodMetrics:
    period: str
    metrics: MetricSummary


@dataclass(frozen=True)
class ExperimentMetrics:
    metadata: ExperimentMetadata
    summary: MetricSummary
    periods: tuple[PeriodMetrics, ...]
    measurements: tuple[DemandMeasurement, ...]
    network_snapshots: tuple[NetworkSnapshot, ...]
    period_order: tuple[str, ...]
