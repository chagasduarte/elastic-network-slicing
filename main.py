import argparse
import random

from algorithms.aco.aco_allocator import AcoAllocator
from algorithms.petic.petic_allocator import PeticAllocator
from algorithms.petic.petic_weight_calculator import PeticWeightCalculator
from algorithms.q_learning.q_learning_allocator import QLearningAllocator
from algorithms.q_learning.q_learning_config import QLearningConfig
from algorithms.sa.simulated_annealing_allocator import SimulatedAnnealingAllocator
from algorithms.sa.simulated_annealing_config import SimulatedAnnealingConfig
from algorithms.sa.simulated_annealing_cost_calculator import (
    SimulatedAnnealingCostCalculator,
)
from algorithms.sa.simulated_annealing_neighbor_generator import (
    SimulatedAnnealingNeighborGenerator,
)
from contracts.germany50_topology import create_germany50_graph
from contracts.slice_allocator import SliceAllocator
from domain.link_allocation import LinkAllocation
from domain.node import Node
from domain.slice_demand import SliceDemand
from domain.slice_request import SliceRequest
from pathfinding.dijkstra_path_finder import DijkstraPathFinder
from services.bandwidth_reservation_service import BandwidthReservationService


def create_allocator(
    algorithm: str,
    reservation_service: BandwidthReservationService,
    seed: int = 42,
) -> SliceAllocator:
    """Constrói o alocador mantendo o mesmo contrato entre os algoritmos."""
    if algorithm == "petic":
        return PeticAllocator(
            path_finder=DijkstraPathFinder(),
            weight_calculator=PeticWeightCalculator(),
        )

    if algorithm == "aco":
        return AcoAllocator(seed=seed)

    if algorithm == "sa":
        config = SimulatedAnnealingConfig()
        random_generator = random.Random(seed)
        return SimulatedAnnealingAllocator(
            path_finder=DijkstraPathFinder(),
            cost_calculator=SimulatedAnnealingCostCalculator(config),
            neighbor_generator=SimulatedAnnealingNeighborGenerator(
                config=config,
                random_generator=random_generator,
            ),
            reservation_service=reservation_service,
            config=config,
            random_generator=random_generator,
        )

    if algorithm == "q-learning":
        return QLearningAllocator(config=QLearningConfig(), seed=seed)

    raise ValueError(f"Algoritmo desconhecido: {algorithm}")


def main(algorithm: str = "petic", seed: int = 42) -> None:
    print(f"Algoritmo de alocação: {algorithm}")
    graph = create_germany50_graph()
    request = SliceRequest(
        id="request-1",
        source=Node("A"),
        destination=Node("L"),
        demands=[
            SliceDemand(id="t1", bandwidth=40),
            SliceDemand(id="t2", bandwidth=50),
            SliceDemand(id="t3", bandwidth=15),
            SliceDemand(id="t4", bandwidth=320),
        ],
    )

    reservation_service = BandwidthReservationService()
    allocator = create_allocator(algorithm, reservation_service, seed)
    previous_result = None

    for demand in request.demands:
        result = allocator.allocate(
            graph=graph,
            request=request,
            demand=demand,
            previous_result=previous_result,
        )

        if result.accepted:
            print(f"Request: {result.request_id}")
            print(f"Demanda: {result.demand_id}")
            print(f"Bandwidth: {demand.bandwidth} Mbps")
            print("Caminho:", " -> ".join(result.path))

            links = graph.get_links_from_path(result.path)
            allocation = LinkAllocation(
                request_id=result.request_id,
                demand_id=result.demand_id,
                bandwidth=result.bandwidth,
            )
            reservation_service.reserve(links=links, allocation=allocation)
        else:
            print(
                "Não foi possível criar a fatia "
                f"para o período {demand.id}."
            )

        print("========================================")
        previous_result = result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Aloca fatias de rede no cenário Germany50.",
    )
    parser.add_argument(
        "--algorithm",
        choices=("petic", "aco", "sa", "q-learning"),
        default="petic",
        help="Algoritmo de alocação (padrão: petic).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Semente dos algoritmos estocásticos (padrão: 42).",
    )
    args = parser.parse_args()
    main(algorithm="aco", seed=args.seed)
