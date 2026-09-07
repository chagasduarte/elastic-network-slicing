import math

from algorithms.petic.petic_weight_calculator import (
    PeticWeightCalculator
)
from contracts.path_finder import PathFinder
from contracts.slice_allocator import SliceAllocator
from domain.link import Link
from domain.network_graph import NetworkGraph
from domain.slice_demand import SliceDemand
from domain.slice_request import SliceRequest
from domain.slice_result import SliceResult


class PeticAllocator(SliceAllocator):

    EPSILON = 0.0001

    def __init__(
        self,
        path_finder: PathFinder,
        weight_calculator: PeticWeightCalculator
    ):
        self._path_finder = path_finder
        self._weight_calculator = weight_calculator

    def allocate(
        self,
        graph: NetworkGraph,
        request: SliceRequest,
        demand: SliceDemand,
        previous_result: SliceResult | None = None
    ) -> SliceResult:

        previous_edges = self._get_previous_edges(
            previous_result
        )

        can_reuse_previous_slice = (
            previous_result is not None
            and previous_result.accepted
            and previous_result.bandwidth >= demand.bandwidth
        )

        def cost_function(link: Link) -> float:

            if not link.supports(demand.id, demand.bandwidth):
                return math.inf

            edge = frozenset([
                link.source.name,
                link.target.name
            ])

            if (
                can_reuse_previous_slice
                and edge in previous_edges
            ):
                return self.EPSILON

            return self._weight_calculator.calculate(
                link,
                demand
            )

        path = self._path_finder.find(
            graph=graph,
            source=request.source.name,
            destination=request.destination.name,
            cost_function=cost_function
        )

        if path is None:
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
            path=path,
            bandwidth=demand.bandwidth
        )

    def _get_previous_edges(
        self,
        previous_result: SliceResult | None
    ) -> set[frozenset[str]]:

        if previous_result is None:
            return set()

        path = previous_result.path

        return {
            frozenset([
                path[index],
                path[index + 1]
            ])
            for index in range(len(path) - 1)
        }