import random

from algorithms.sa.simulated_annealing_config import (
    SimulatedAnnealingConfig
)
from domain.network_graph import NetworkGraph
from domain.slice_demand import SliceDemand


class SimulatedAnnealingNeighborGenerator:

    def __init__(
        self,
        config: SimulatedAnnealingConfig,
        random_generator: random.Random
    ):
        self._config = config
        self._random = random_generator

    def generate(
        self,
        graph: NetworkGraph,
        current_path: list[str],
        demand: SliceDemand
    ) -> list[str] | None:

        if len(current_path) < 2:
            return None

        for _ in range(
            self._config.neighbor_attempts
        ):

            pivot_index = (
                self._random.randint(
                    0,
                    len(current_path) - 2
                )
            )

            prefix = current_path[
                :pivot_index + 1
            ]

            pivot_name = prefix[-1]

            pivot_node = graph.get_node(
                pivot_name
            )

            if pivot_node is None:
                continue

            destination = current_path[-1]

            visited = set(prefix)

            suffix = self._find_suffix(
                graph=graph,
                current_name=pivot_name,
                destination_name=destination,
                demand=demand,
                visited=visited,
                remaining_steps=(
                    self._config.max_neighbor_steps
                )
            )

            if suffix is None:
                continue

            candidate = (
                prefix[:-1]
                + suffix
            )

            if candidate == current_path:
                continue

            return candidate

        return None

    def _find_suffix(
        self,
        graph: NetworkGraph,
        current_name: str,
        destination_name: str,
        demand: SliceDemand,
        visited: set[str],
        remaining_steps: int
    ) -> list[str] | None:

        if (
            current_name
            == destination_name
        ):
            return [
                current_name
            ]

        if remaining_steps <= 0:
            return None

        current_node = graph.get_node(
            current_name
        )

        if current_node is None:
            return None

        neighbors = list(
            graph.get_neighbors(
                current_node
            )
        )

        self._random.shuffle(
            neighbors
        )

        for neighbor, link in neighbors:

            neighbor_name = (
                neighbor.name
            )

            if neighbor_name in visited:
                continue

            if not link.supports(
                demand.id,
                demand.bandwidth
            ):
                continue

            visited.add(
                neighbor_name
            )

            suffix = self._find_suffix(
                graph=graph,
                current_name=neighbor_name,
                destination_name=destination_name,
                demand=demand,
                visited=visited,
                remaining_steps=(
                    remaining_steps - 1
                )
            )

            if suffix is not None:

                return [
                    current_name,
                    *suffix
                ]

            visited.remove(
                neighbor_name
            )

        return None