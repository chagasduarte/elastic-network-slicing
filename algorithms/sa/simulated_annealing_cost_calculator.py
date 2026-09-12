import math

from algorithms.sa.simulated_annealing_config import (
    SimulatedAnnealingConfig
)
from domain.network_graph import NetworkGraph
from domain.slice_demand import SliceDemand


class SimulatedAnnealingCostCalculator:

    def __init__(
        self,
        config: SimulatedAnnealingConfig
    ):
        self._config = config

    def calculate(
        self,
        graph: NetworkGraph,
        path: list[str],
        demand: SliceDemand,
        previous_path: list[str] | None = None
    ) -> float:

        links = graph.get_links_from_path(
            path
        )

        if not links:
            return math.inf

        utilizations: list[float] = []

        for link in links:

            allocated = (
                link.allocated_bandwidth_at(
                    demand.id
                )
            )

            utilization = (
                allocated
                + demand.bandwidth
            ) / link.capacity

            if utilization > 1:
                return math.inf

            utilizations.append(
                utilization
            )

        hop_cost = self._hop_cost(
            graph,
            path
        )

        average_utilization = (
            sum(utilizations)
            / len(utilizations)
        )

        bottleneck_utilization = max(
            utilizations
        )

        path_change = self._path_change(
            path,
            previous_path
        )

        return (
            self._config.hop_weight
            * hop_cost

            + self._config.avg_utilization_weight
            * average_utilization

            + self._config.bottleneck_weight
            * bottleneck_utilization

            + self._config.path_change_weight
            * path_change
        )

    def _hop_cost(
        self,
        graph: NetworkGraph,
        path: list[str]
    ) -> float:

        number_of_hops = (
            len(path) - 1
        )

        maximum_possible_hops = max(
            1,
            len(graph.nodes) - 1
        )

        return (
            number_of_hops
            / maximum_possible_hops
        )

    def _path_change(
        self,
        current_path: list[str],
        previous_path: list[str] | None
    ) -> float:

        if not previous_path:
            return 0.0

        current_edges = self._edge_set(
            current_path
        )

        previous_edges = self._edge_set(
            previous_path
        )

        union = (
            current_edges
            | previous_edges
        )

        if not union:
            return 0.0

        intersection = (
            current_edges
            & previous_edges
        )

        similarity = (
            len(intersection)
            / len(union)
        )

        return (
            1.0 - similarity
        )

    def _edge_set(
        self,
        path: list[str]
    ) -> set[tuple[str, str]]:

        edges: set[
            tuple[str, str]
        ] = set()

        for index in range(
            len(path) - 1
        ):

            source = path[index]
            destination = path[
                index + 1
            ]

            edge = tuple(
                sorted(
                    (
                        source,
                        destination
                    )
                )
            )

            edges.add(edge)

        return edges