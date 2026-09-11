# algorithms/simulated_annealing/simulated_annealing_cost_calculator.py

from algorithms.simulated_annealing.simulated_annealing_config import (
    SimulatedAnnealingConfig
)
from domain.network_graph import NetworkGraph
from domain.node import Node


class SimulatedAnnealingCostCalculator:

    def __init__(
        self,
        config: SimulatedAnnealingConfig
    ):
        self.config = config

    def calculate(
        self,
        graph: NetworkGraph,
        path: list[Node],
        demand_id: str,
        bandwidth: int,
        previous_path: list[Node] | None = None
    ) -> float:

        links = graph.get_links_from_path(path)

        if not links:
            return 0.0

        hop_cost = self._calculate_hop_cost(
            graph,
            links
        )

        utilizations = self._calculate_utilizations(
            links,
            demand_id,
            bandwidth
        )

        if not utilizations:
            return float("inf")

        average_utilization = (
            sum(utilizations) / len(utilizations)
        )

        bottleneck_utilization = max(utilizations)

        path_change = self._calculate_path_change(
            path,
            previous_path
        )

        cost = (
            self.config.hop_weight
            * hop_cost

            + self.config.avg_utilization_weight
            * average_utilization

            + self.config.bottleneck_weight
            * bottleneck_utilization

            + self.config.path_change_weight
            * path_change
        )

        return cost

    def _calculate_hop_cost(
        self,
        graph: NetworkGraph,
        links
    ) -> float:

        maximum_possible_hops = max(
            1,
            graph.node_count - 1
        )

        return (
            len(links)
            / maximum_possible_hops
        )

    def _calculate_utilizations(
        self,
        links,
        demand_id: str,
        bandwidth: int
    ) -> list[float]:

        utilizations: list[float] = []

        for link in links:

            allocated = (
                link.allocated_bandwidth_at(
                    demand_id
                )
            )

            utilization = (
                allocated + bandwidth
            ) / link.capacity

            if utilization > 1:
                return []

            utilizations.append(
                utilization
            )

        return utilizations

    def _calculate_path_change(
        self,
        path: list[Node],
        previous_path: list[Node] | None
    ) -> float:

        if not previous_path:
            return 0.0

        current_edges = self._edge_set(path)
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

        return 1.0 - similarity

    def _edge_set(
        self,
        path: list[Node]
    ) -> set[tuple[str, str]]:

        edges: set[tuple[str, str]] = set()

        for index in range(
            len(path) - 1
        ):
            source = path[index].id
            target = path[index + 1].id

            edge = tuple(
                sorted(
                    (source, target)
                )
            )

            edges.add(edge)

        return edges