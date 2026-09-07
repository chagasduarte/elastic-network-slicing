from algorithms.petic.petic_allocator import PeticAllocator
from algorithms.petic.petic_weight_calculator import PeticWeightCalculator
from domain.link_allocation import LinkAllocation
from domain.network_graph import NetworkGraph
from domain.slice_demand import SliceDemand
from domain.slice_request import SliceRequest
from pathfinding.dijkstra_path_finder import DijkstraPathFinder
from services.bandwidth_reservation_service import BandwidthReservationService
from contracts.create_topo import create_topo

def main():
    # ---------------------------------------------------------
    # 1. Criação da topologia
    # ---------------------------------------------------------

    graph = create_topo()

    
    # ---------------------------------------------------------
    # 2. Criação da requisição
    # ---------------------------------------------------------

    request = SliceRequest(
        id="request-1",
        source="A",
        destination="E",
        demands=[
            SliceDemand(
                id="t1",
                bandwidth=40
            ),
            SliceDemand(
                id="t2",
                bandwidth=60
            ),
            SliceDemand(
                id="t3",
                bandwidth=80
            ),
            SliceDemand(
                id="t4",
                bandwidth=30
            )
        ]
    )

    # ---------------------------------------------------------
    # 3. Dependências do PETIC
    # ---------------------------------------------------------

    path_finder = DijkstraPathFinder()

    weight_calculator = PeticWeightCalculator()

    petic = PeticAllocator(
        path_finder=path_finder,
        weight_calculator=weight_calculator
    )

    reservation_service = BandwidthReservationService()

    # ---------------------------------------------------------
    # 4. Executa PETIC para t1
    # ---------------------------------------------------------

    demand = request.demand_at("t1")

    result = petic.allocate(
        graph=graph,
        request=request,
        demand=demand
    )

    # ---------------------------------------------------------
    # 5. Exibe decisão
    # ---------------------------------------------------------

    print("\n--- RESULTADO PETIC ---")

    print(f"Request: {result.request_id}")
    print(f"Demanda: {result.demand_id}")
    print(f"Bandwidth: {result.bandwidth} Mbps")
    print(f"Aceita: {result.accepted}")

    if not result.accepted:
        print("Não foi possível criar a fatia.")
        return

    print(
        "Caminho:",
        " -> ".join(result.path)
    )
    print(graph.get_links())

    # ---------------------------------------------------------
    # 6. Converte o caminho para objetos Link
    # ---------------------------------------------------------

    links = graph.get_links_from_path(
        result.path
    )

    # ---------------------------------------------------------
    # 7. Cria a alocação
    # ---------------------------------------------------------

    allocation = LinkAllocation(
        request_id=result.request_id,
        demand_id=result.demand_id,
        bandwidth=result.bandwidth
    )

    # ---------------------------------------------------------
    # 8. Reserva a largura de banda
    # ---------------------------------------------------------

    reservation_service.reserve(
        links=links,
        allocation=allocation
    )

    # ---------------------------------------------------------
    # 9. Mostra estado da rede depois da alocação
    # ---------------------------------------------------------

    print("\n--- ESTADO DOS ENLACES ---")

    for link in graph.links:
        print(
            f"{link.source} <-> {link.target} | "
            f"Capacidade: {link.capacity} Mbps | "
            f"Alocado: {link.allocated_bandwidth} Mbps | "
            f"Disponível: {link.available_bandwidth} Mbps"
        )


if __name__ == "__main__":
    main()