import random

from contracts.slice_allocator import SliceAllocator
from domain.link import Link
from domain.network_graph import NetworkGraph
from domain.node import Node
from domain.slice_demand import SliceDemand
from domain.slice_request import SliceRequest
from domain.slice_result import SliceResult
import math

class AcoAllocator(SliceAllocator):

    def __init__(
        self,
        ants_count: int = 20,
        iterations: int = 50,
        alpha: float = 1.0,
        beta: float = 2.0,
        evaporation_rate: float = 0.1,
        initial_pheromone: float = 1.0,
        pheromone_deposit: float = 1.0,
        seed: int | None = None
    ):
        self._ants_count = ants_count
        self._iterations = iterations

        self._alpha = alpha
        self._beta = beta

        self._evaporation_rate = (
            evaporation_rate
        )

        self._initial_pheromone = (
            initial_pheromone
        )

        self._pheromone_deposit = (
            pheromone_deposit
        )

        self._random = random.Random(seed)

    def allocate(
        self,
        graph: NetworkGraph,
        request: SliceRequest,
        demand: SliceDemand,
        previous_result: SliceResult | None = None
    ) -> SliceResult:

        pheromones = (
            self._initialize_pheromones(
                graph
            )
        )

        best_path: list[str] | None = None
        best_cost = float("inf")

        for iteration in range(
            self._iterations
        ):

            solutions: list[
                tuple[list[str], float]
            ] = []

            for ant_index in range(
                self._ants_count
            ):

                path = self._build_ant_path(
                    graph=graph,
                    source=request.source,
                    destination=request.destination,
                    demand=demand,
                    pheromones=pheromones
                )

                if path is None:
                    continue

                cost = self._calculate_path_cost(
                    graph=graph,
                    path=path,
                    demand=demand
                )
                
                print(
                    f"Formiga {ant_index} | "
                    f"Caminho: {' -> '.join(path)} | "
                    f"Custo: {cost:.4f}"
                )

                solutions.append(
                    (
                        path,
                        cost
                    )
                )

                if cost < best_cost:
                    best_cost = cost
                    best_path = path

            self._evaporate_pheromones(
                pheromones
            )

            for path, cost in solutions:

                self._deposit_pheromone(
                    pheromones=pheromones,
                    path=path,
                    cost=cost
                )

        if best_path is None:
            return SliceResult(
                request_id=request.id,
                demand_id=demand.id,
                accepted=False,
                path=[],
                bandwidth=0
            )

        return SliceResult(
            request_id=request.id,
            demand_id=demand.id,
            accepted=True,
            path=best_path,
            bandwidth=demand.bandwidth
        )

    def _build_ant_path(
        self,
        graph: NetworkGraph,
        source: Node,
        destination: Node,
        demand: SliceDemand,
        pheromones: dict[
            frozenset[str],
            float
        ]
    ) -> list[str] | None:

        current_node = source

        visited_nodes: set[Node] = {
            source
        }

        path: list[Node] = [
            source
        ]

        while current_node != destination:

            feasible_links = (
                self._get_feasible_links(
                    graph=graph,
                    current_node=current_node,
                    demand=demand,
                    visited_nodes=visited_nodes
                )
            )

            if not feasible_links:
                return None

            options = []

            total_attractiveness = 0.0

            for link in feasible_links:

                if link.source == current_node:
                    next_node = link.target
                else:
                    next_node = link.source

                pheromone = pheromones[
                    self._edge_key(link)
                ]

                heuristic = (
                    self._calculate_heuristic(
                        link,
                        demand
                    )
                )

                attractiveness = (
                    pheromone ** self._alpha
                    * heuristic ** self._beta
                )

                options.append(
                    (
                        link,
                        next_node,
                        attractiveness
                    )
                )

                total_attractiveness += (
                    attractiveness
                )

            if total_attractiveness == 0:
                return None

            probabilities = []

            for (
                link,
                next_node,
                attractiveness
            ) in options:

                probability = (
                    attractiveness
                    / total_attractiveness
                )

                probabilities.append(
                    (
                        link,
                        next_node,
                        probability
                    )
                )

            (
                selected_link,
                next_node,
                probability
            ) = self._random.choices(
                probabilities,
                weights=[
                    probability
                    for _, _, probability
                    in probabilities
                ],
                k=1
            )[0]

            path.append(next_node)

            visited_nodes.add(next_node)

            current_node = next_node

        return [
            node.name
            for node in path
        ]

    def _get_feasible_links(
        self,
        graph: NetworkGraph,
        current_node: Node,
        demand: SliceDemand,
        visited_nodes: set[Node]
    ) -> list[Link]:

        feasible_links: list[Link] = []

        for neighbor, link in graph.get_neighbors(
            current_node
        ):

            if neighbor in visited_nodes:
                continue

            if not link.supports(
                demand.id,
                demand.bandwidth
            ):
                continue

            feasible_links.append(link)

        return feasible_links

    def _calculate_heuristic(
        self,
        link: Link,
        demand: SliceDemand
    ) -> float:

        available = (
            link.available_bandwidth_at(
                demand.id
            )
        )

        if available < demand.bandwidth:
            return 0.0

        return (
            available
            / demand.bandwidth
        )

    def _calculate_path_cost(
        self,
        graph: NetworkGraph,
        path: list[str],
        demand: SliceDemand
    ) -> float:

        links = graph.get_links_from_path(path)

        cost = 0.0

        for link in links:

            available = link.available_bandwidth_at(
                demand.id
            )
            

            cost += math.exp(
                demand.bandwidth / available
            )

        return cost

    def _initialize_pheromones(
        self,
        graph: NetworkGraph
    ) -> dict[frozenset[str], float]:

        pheromones = {}

        for link in graph.links:

            pheromones[
                self._edge_key(link)
            ] = self._initial_pheromone

        return pheromones

    def _evaporate_pheromones(
        self,
        pheromones: dict[
            frozenset[str],
            float
        ]
    ) -> None:

        for edge in pheromones:

            pheromones[edge] *= (
                1.0
                - self._evaporation_rate
            )

    def _deposit_pheromone(
        self,
        pheromones: dict[
            frozenset[str],
            float
        ],
        path: list[str],
        cost: float
    ) -> None:

        amount = (
            self._pheromone_deposit
            / cost
        )

        for index in range(
            len(path) - 1
        ):

            edge = frozenset([
                path[index],
                path[index + 1]
            ])

            pheromones[edge] += amount

    def _edge_key(
        self,
        link: Link
    ) -> frozenset[str]:

        return frozenset([
            link.source.name,
            link.target.name
        ])