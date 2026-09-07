from abc import ABC, abstractmethod
from collections.abc import Callable

from domain.link import Link
from domain.network_graph import NetworkGraph
from domain.node import Node

class PathFinder(ABC):

    @abstractmethod
    def find(
        self,
        graph: NetworkGraph,
        source: Node,
        destination: Node,
        cost_function: Callable[[Link], float]
    ) -> list[str] | None:
        pass