from contracts.slice_allocator import SliceAllocator
from domain.link import Link
from domain.node import Node
from domain.network_graph import NetworkGraph
from domain.slice_demand import SliceDemand
from domain.slice_request import SliceRequest
from domain.slice_result import SliceResult

import random


class AcoAllocator(SliceAllocator):

    def __init__(
        self,
        ants_count: int = 20,
        iterations: int = 50,
        alpha: float = 1.0,
        beta: float = 2.0,
        evaporation_rate: float = 0.1,
        initial_pheromone: float = 1.0
    ):
        self._ants_count = ants_count
        self._iterations = iterations

        self._alpha = alpha
        self._beta = beta

        self._evaporation_rate = evaporation_rate

        self._initial_pheromone = initial_pheromone

    def allocate(
        self,
        graph: NetworkGraph,
        request: SliceRequest,
        demand: SliceDemand,
        previous_result: SliceResult | None = None
    ) -> SliceResult:
 
        pheromones = self._initialize_pheromones(
            graph.links
        )

        current_node = request.source

        path: list[str] = [current_node]
        
        visited_nodes: set[Node] = {
            current_node
        }

        while current_node.name != request.destination.name:

            print("Nó atual: ", current_node.name)

            feasible_links = self._get_feasible_links(
                graph=graph,
                current_node=current_node,
                demand=demand,
                visited_nodes=visited_nodes
            )

            if not feasible_links:
                print("Formiga ficou sem caminhos possíveis.")
                return None

            options = []
            total_attractiveness = 0.0

            
            for link in feasible_links:
                if link.source == current_node:
                    next_node = link.target
                else:
                    next_node = link.source

                pheromone = pheromones[self._edge_key(link)]

                heuristica = self._calculate_heuristic(link, demand)

                attractiveness = (pheromone ** self._alpha * heuristica ** self._beta) 

                total_attractiveness += attractiveness
                               
                options.append((link, next_node, attractiveness))

            probabilities = []

            for link, next_node, attractiveness in options:
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

            selected = random.choices(
                probabilities,
                weights=[
                    probability
                    for _, _, probability in probabilities
                ],
                k=1
            )[0]

            selected_link, next_node, probability = selected

            path.append(next_node)

            visited_nodes.add(next_node)

            current_node = next_node

        return SliceResult(
            request_id=request.id,
            demand_id=demand.id,
            accepted=False,
            path=path,
            bandwidth=0
        )

    def _initialize_pheromones(
        self,
        links: list[Link]
    ) -> dict[frozenset[str], float]:

        pheromones: dict[frozenset[str], float] = {}

        for link in links:

            edge = self._edge_key(link)

            pheromones[edge] = (
                self._initial_pheromone
            )

        return pheromones

    def _edge_key(
        self,
        link: Link
    ) -> frozenset[str]:

        return frozenset([
            link.source.name,
            link.target.name
        ])

    def _get_feasible_links(
        self,
        graph: NetworkGraph,
        current_node: Node,
        demand: SliceDemand,
        visited_nodes: set[Node]
    ) -> list[Link]:
        print("  ->Buscando caminhos Possíveis saindo de: ", current_node.name)
        print("  ->Demanda: ", demand.bandwidth)

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

        print("  ->Caminhos Encontrados: ", len(feasible_links))

        return feasible_links
        

    def _calculate_heuristic(
        self,
        link: Link,
        demand: SliceDemand
    ) -> float:

        available_bandwidth = link.available_bandwidth_at(
            demand.id
        )

        if available_bandwidth < demand.bandwidth:
            return 0.0

        return (
            available_bandwidth
            / demand.bandwidth
        )