from algorithms.petic.petic_allocator import PeticAllocator
from algorithms.petic.petic_weight_calculator import PeticWeightCalculator
from domain.link_allocation import LinkAllocation
from domain.slice_demand import SliceDemand
from domain.slice_request import SliceRequest
from pathfinding.dijkstra_path_finder import DijkstraPathFinder
from services.bandwidth_reservation_service import BandwidthReservationService
from contracts.create_topo import create_test_graph
from domain.node import Node


def main():
    # ---------------------------------------------------------
    # 1. Criação da topologia
    # ---------------------------------------------------------

    graph = create_test_graph()

    # ---------------------------------------------------------
    # 2. Criação da requisição
    # ---------------------------------------------------------

    request = SliceRequest(
        id="request-1",
        source=Node("A"),
        destination=Node("L"),
        demands=[
            SliceDemand(
                id="t1",
                bandwidth=80
            ),
            SliceDemand(
                id="t2",
                bandwidth=50
            ),
            SliceDemand(
                id="t3",
                bandwidth=15
            ),
            SliceDemand(
                id="t4",
                bandwidth=105
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
    # 4. Guarda o resultado do período anterior
    # ---------------------------------------------------------

    previous_result = None

    # ---------------------------------------------------------
    # 5. Executa todos os períodos
    # ---------------------------------------------------------

    for demand in request.demands:

        result = petic.allocate(
            graph=graph,
            request=request,
            demand=demand,
            previous_result=previous_result
        )

        # -----------------------------------------------------
        # 6. Exibe decisão do período
        # -----------------------------------------------------

        print(f"Request: {result.request_id}")
        print(f"Demanda: {result.demand_id}")
        print(f"Bandwidth: {demand.bandwidth} Mbps")

        if result.accepted:

            print(
                "Caminho:",
                " -> ".join(result.path)
            )

            # -------------------------------------------------
            # 7. Converte caminho para Links
            # -------------------------------------------------

            links = graph.get_links_from_path(
                result.path
            )

            # -------------------------------------------------
            # 8. Cria a alocação
            # -------------------------------------------------

            allocation = LinkAllocation(
                request_id=result.request_id,
                demand_id=result.demand_id,
                bandwidth=result.bandwidth
            )

            # -------------------------------------------------
            # 9. Reserva largura de banda
            # -------------------------------------------------

            reservation_service.reserve(
                links=links,
                allocation=allocation
            )

        else:
            print(
                "Não foi possível criar a fatia "
                f"para o período {demand.id}."
            )
        print("========================================")
        
        previous_result = result


if __name__ == "__main__":
    main()