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
from domain.link import Link
from domain.network_graph import NetworkGraph
from domain.slice_demand import SliceDemand
from domain.slice_request import SliceRequest
from domain.slice_result import SliceResult
from domain.link_allocation import LinkAllocation
from services.bandwidth_reservation_service import (
    BandwidthReservationService
)


class SimulatedAnnealingAllocator(SliceAllocator):

    def __init__(
        self,
        path_finder: PathFinder,
        cost_calculator: SimulatedAnnealingCostCalculator,
        neighbor_generator: SimulatedAnnealingNeighborGenerator,
        reservation_service: BandwidthReservationService,
        config: SimulatedAnnealingConfig,
        random_generator: random.Random
    ):
        self._path_finder = path_finder
        self._cost_calculator = cost_calculator
        self._neighbor_generator = neighbor_generator
        self._reservation_service = reservation_service
        self._config = config
        self._random = random_generator

    def allocate(
        self,
        graph: NetworkGraph,
        request: SliceRequest,
        demand: SliceDemand,
        previous_result: SliceResult | None = None
    ) -> SliceResult:

        initial_path = self._find_initial_path(
            graph,
            request,
            demand
        )

        if initial_path is None:
            return self._rejected_result(
                request,
                demand
            )

        current_path = initial_path

        current_cost = self._cost_calculator.calculate(
            graph=graph,
            path=current_path,
            demand=demand,
            previous_path=(
                previous_result.path
                if previous_result is not None
                and previous_result.accepted
                else None
            )
        )

        best_path = current_path.copy()
        best_cost = current_cost

        temperature = (
            self._config.initial_temperature
        )

        iteration = 0

        while (
            temperature
            > self._config.minimum_temperature
            and iteration
            < self._config.max_iterations
        ):

            neighbor_path = (
                self._neighbor_generator.generate(
                    graph=graph,
                    current_path=current_path,
                    demand=demand
                )
            )

            if neighbor_path is not None:

                neighbor_cost = (
                    self._cost_calculator.calculate(
                        graph=graph,
                        path=neighbor_path,
                        demand=demand,
                        previous_path=(
                            previous_result.path
                            if previous_result is not None
                            and previous_result.accepted
                            else None
                        )
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
                    current_path = (
                        neighbor_path
                    )

                    current_cost = (
                        neighbor_cost
                    )

                if current_cost < best_cost:
                    best_path = (
                        current_path.copy()
                    )

                    best_cost = current_cost

            temperature = (
                self._cool(
                    temperature
                )
            )

            iteration += 1

        links = graph.get_links_from_path(
            best_path
        )

        allocation = LinkAllocation(
            request_id=request.id,
            demand_id=demand.id,
            bandwidth=demand.bandwidth
        )

        self._reservation_service.reserve(
            links,
            allocation
        )

        return SliceResult(
            request_id=request.id,
            demand_id=demand.id,
            accepted=True,
            path=best_path,
            bandwidth=demand.bandwidth
        )

    def _find_initial_path(
        self,
        graph: NetworkGraph,
        request: SliceRequest,
        demand: SliceDemand
    ) -> list[str] | None:

        def cost_function(
            link: Link
        ) -> float:

            if not link.supports(
                demand.id,
                demand.bandwidth
            ):
                return math.inf

            return 1.0

        return self._path_finder.find(
            graph=graph,
            source=request.source.name,
            destination=request.destination.name,
            cost_function=cost_function
        )

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

        return (
            self._random.random()
            < probability
        )

    def _cool(
        self,
        temperature: float
    ) -> float:

        return (
            temperature
            * self._config.cooling_rate
        )

    def _rejected_result(
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