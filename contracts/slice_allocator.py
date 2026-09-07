from abc import ABC, abstractmethod

from domain.network_graph import NetworkGraph
from domain.slice_request import SliceRequest
from domain.slice_demand import SliceDemand
from domain.slice_result import SliceResult


class SliceAllocator(ABC):

    @abstractmethod
    def allocate(
        self,
        graph: NetworkGraph,
        request: SliceRequest,
        demand: SliceDemand,
        previous_result: SliceResult | None = None
    ) -> SliceResult:
        pass