import heapq
import math
from itertools import count
from collections.abc import Callable

from contracts.path_finder import PathFinder
from domain.link import Link
from domain.network_graph import NetworkGraph
from domain.node import Node


class DijkstraPathFinder(PathFinder):

    def find(
        self,
        graph: NetworkGraph,
        source: str,
        destination: str,
        cost_function: Callable[[Link], float]
    ) -> list[str] | None:

        source_node = graph.get_node(source)
        destination_node = graph.get_node(destination)

        if source_node is None:
            raise ValueError(
                f"Nó de origem '{source}' não encontrado."
            )

        if destination_node is None:
            raise ValueError(
                f"Nó de destino '{destination}' não encontrado."
            )

        distances: dict[Node, float] = {
            node: math.inf
            for node in graph.nodes
        }

        previous: dict[Node, Node | None] = {
            node: None
            for node in graph.nodes
        }

        distances[source_node] = 0

        counter = count()

        queue = [
            (
                0,
                next(counter),
                source_node
            )
        ]

        while queue:
            current_cost, _, current_node = heapq.heappop(
                queue
            )

            if current_node == destination_node:
                break

            if current_cost > distances[current_node]:
                continue

            for neighbor, link in graph.get_neighbors(
                current_node
            ):
                link_cost = cost_function(link)

                if math.isinf(link_cost):
                    continue

                new_cost = current_cost + link_cost

                if new_cost < distances[neighbor]:
                    distances[neighbor] = new_cost
                    previous[neighbor] = current_node

                    heapq.heappush(
                        queue,
                        (
                            new_cost,
                            next(counter),
                            neighbor
                        )
                    )

        if math.isinf(
            distances[destination_node]
        ):
            return None

        path: list[Node] = []

        current: Node | None = destination_node

        while current is not None:
            path.append(current)
            current = previous[current]

        path.reverse()

        return [
            node.name
            for node in path
        ]