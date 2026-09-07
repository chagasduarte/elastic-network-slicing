import heapq
import math
from collections.abc import Callable

from contracts.path_finder import PathFinder
from domain.link import Link
from domain.network_graph import NetworkGraph


class DijkstraPathFinder(PathFinder):

    def find(
        self,
        graph: NetworkGraph,
        source: str,
        destination: str,
        cost_function: Callable[[Link], float]
    ) -> list[str] | None:

        distances = {
            node: math.inf
            for node in graph.nodes
        }

        previous: dict[str, str | None] = {
            node: None
            for node in graph.nodes
        }

        distances[source] = 0

        queue = [
            (0, source)
        ]

        while queue:
            current_cost, current_node = heapq.heappop(queue)

            if current_node == destination:
                break

            if current_cost > distances[current_node]:
                continue

            for neighbor, link in graph.get_neighbors(current_node):

                link_cost = cost_function(link)

                if math.isinf(link_cost):
                    continue

                new_cost = (
                    current_cost
                    + link_cost
                )

                if new_cost < distances[neighbor]:

                    distances[neighbor] = new_cost
                    previous[neighbor] = current_node

                    heapq.heappush(
                        queue,
                        (new_cost, neighbor)
                    )

        if math.isinf(distances[destination]):
            return None

        path = []

        current = destination

        while current is not None:
            path.append(current)
            current = previous[current]

        path.reverse()

        return path