# algorithms/simulated_annealing/simulated_annealing_neighbor_generator.py

import random

from algorithms.simulated_annealing.simulated_annealing_config import (
    SimulatedAnnealingConfig
)
from domain.network_graph import NetworkGraph
from domain.node import Node


class SimulatedAnnealingNeighborGenerator:

    def __init__(
        self,
        config: SimulatedAnnealingConfig,
        random_generator: random.Random
    ):
        self.config = config
        self.random = random_generator

    def generate(
        self,
        graph: NetworkGraph,
        current_path: list[Node],
        source: Node,
        destination: Node,
        demand_id: str,
        bandwidth: int
    ) -> list[Node] | None:

        if len(current_path) < 2:
            return None

        for _ in range(
            self.config.neighbor_attempts
        ):

            pivot_index = self.random.randint(
                0,
                len(current_path) - 2
            )

            prefix = current_path[
                :pivot_index + 1
            ]

            pivot = prefix[-1]

            visited = set(prefix)

            suffix = self._find_random_suffix(
                graph=graph,
                current=pivot,
                destination=destination,
                demand_id=demand_id,
                bandwidth=bandwidth,
                visited=visited,
                remaining_steps=(
                    self.config.max_neighbor_steps
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

    def _find_random_suffix(
        self,
        graph: NetworkGraph,
        current: Node,
        destination: Node,
        demand_id: str,
        bandwidth: int,
        visited: set[Node],
        remaining_steps: int
    ) -> list[Node] | None:

        if current == destination:
            return [current]

        if remaining_steps <= 0:
            return None

        neighbors = graph.get_neighbors(
            current
        )

        candidates: list[Node] = []

        for neighbor in neighbors:

            if neighbor in visited:
                continue

            link = graph.get_link(
                current,
                neighbor
            )

            if link is None:
                continue

            if not link.supports(
                demand_id,
                bandwidth
            ):
                continue

            candidates.append(
                neighbor
            )

        self.random.shuffle(candidates)

        for neighbor in candidates:

            visited.add(neighbor)

            suffix = self._find_random_suffix(
                graph=graph,
                current=neighbor,
                destination=destination,
                demand_id=demand_id,
                bandwidth=bandwidth,
                visited=visited,
                remaining_steps=(
                    remaining_steps - 1
                )
            )

            if suffix is not None:
                return [
                    current,
                    *suffix
                ]

            visited.remove(neighbor)

        return None