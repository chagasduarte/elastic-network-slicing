# algorithms/simulated_annealing/simulated_annealing_allocator.py

import math
import random

from algorithms.sa.simulated_annealing_config import (
    SimulatedAnnealingConfig
)
from algorithms.sa.simulated_annealing_cost_calculator import (
    SimulatedAnnealingCostCalculator
)
from algorithms.sa.simulated_annealing_neighbor_generator import (
    SimulatedAnnealingNeighborGenerator
)
from contracts.path_finder import PathFinder
from contracts.slice_allocator import SliceAllocator
from domain.network_graph import NetworkGraph
from domain.node import Node
from domain.slice_demand import SliceDemand
from domain.slice_request import SliceRequest
from domain.slice_result import SliceResult
from services.bandwidth_reservation_service import (
    BandwidthReservationService
)


class SimulatedAnnealingAllocator(
    SliceAllocator
):

    def __init__(
        self,
        path_finder: PathFinder,
        cost_calculator: SimulatedAnnealingCostCalculator,
        neighbor_generator: SimulatedAnnealingNeighborGenerator,
        reservation_service: BandwidthReservationService,
        config: SimulatedAnnealingConfig,
        random_generator: random.Random
    ):
        self.path_finder = path_finder
        self.cost_calculator = cost_calculator
        self.neighbor_generator = (
            neighbor_generator
        )
        self.reservation_service = (
            reservation_service
        )
        self.config = config
        self.random = random_generator

    def allocate(
        self,
        graph: NetworkGraph,
        request: SliceRequest,
        demand: SliceDemand,
        previous_result: SliceResult | None = None
    ) -> list[SliceResult]:

        results: list[SliceResult] = []

        previous_path: list[Node] | None = None

        for demand in request.demands:

            best_path = self._optimize(
                graph=graph,
                request=request,
                demand=demand,
                previous_path=previous_path
            )

            if best_path is None:

                results.append(
                    self._create_rejected_result(
                        request,
                        demand
                    )
                )

                continue

            links = graph.get_links_from_path(
                best_path
            )

            self.reservation_service.reserve(
                links,
                demand.bandwidth
            )

            results.append(
                SliceResult(
                    request_id=request.id,
                    period_id=demand.id,
                    accepted=True,
                    path=[
                        node.id
                        for node
                        in best_path
                    ],
                    bandwidth=demand.bandwidth
                )
            )

            previous_path = best_path

        return results

    def _optimize(
        self,
        graph: NetworkGraph,
        request: SliceRequest,
        demand: SliceDemand,
        previous_path: list[Node] | None
    ) -> list[Node] | None:

        current_path = (
            self.path_finder.find_path(
                graph=graph,
                source=request.source,
                destination=request.destination,
                demand_id=demand.id,
                bandwidth=demand.bandwidth
            )
        )

        if not current_path:
            return None

        current_cost = (
            self.cost_calculator.calculate(
                graph=graph,
                path=current_path,
                demand_id=demand.id,
                bandwidth=demand.bandwidth,
                previous_path=previous_path
            )
        )

        best_path = list(current_path)
        best_cost = current_cost

        temperature = (
            self.config.initial_temperature
        )

        iteration = 0

        while (
            temperature
            > self.config.minimum_temperature
            and iteration
            < self.config.max_iterations
        ):

            neighbor = (
                self.neighbor_generator.generate(
                    graph=graph,
                    current_path=current_path,
                    source=request.source,
                    destination=(
                        request.destination
                    ),
                    demand_id=demand.id,
                    bandwidth=demand.bandwidth
                )
            )

            if neighbor is not None:

                neighbor_cost = (
                    self.cost_calculator.calculate(
                        graph=graph,
                        path=neighbor,
                        demand_id=demand.id,
                        bandwidth=demand.bandwidth,
                        previous_path=previous_path
                    )
                )

                delta = (
                    neighbor_cost
                    - current_cost
                )

                if self._should_accept(
                    delta,
                    temperature
                ):
                    current_path = neighbor
                    current_cost = neighbor_cost

                if current_cost < best_cost:
                    best_path = list(
                        current_path
                    )

                    best_cost = (
                        current_cost
                    )

            temperature *= (
                self.config.cooling_rate
            )

            iteration += 1

        return best_path

    def _should_accept(
        self,
        delta: float,
        temperature: float
    ) -> bool:

        if delta <= 0:
            return True

        probability = math.exp(
            -delta / temperature
        )

        random_value = (
            self.random.random()
        )

        return (
            random_value
            < probability
        )

    def _create_rejected_result(
        self,
        request: SliceRequest,
        demand: SliceDemand
    ) -> SliceResult:

        return SliceResult(
            request_id=request.id,
            period_id=demand.id,
            accepted=False,
            path=[],
            bandwidth=demand.bandwidth
        )