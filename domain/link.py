from dataclasses import dataclass, field

from domain.link_allocation import LinkAllocation
from domain.node import Node

@dataclass
class Link:
    source: Node
    target: Node
    capacity: int
    allocations: list[LinkAllocation] = field(
        default_factory=list
    )

    def __post_init__(self):
        if self.capacity <= 0:
            raise ValueError(
                "A capacidade do enlace deve ser maior que zero."
            )

    @property
    def allocated_bandwidth(self) -> int:
        return sum(
            allocation.bandwidth
            for allocation in self.allocations
        )

    @property
    def available_bandwidth(self) -> int:
        return self.capacity - self.allocated_bandwidth

    def supports(self, bandwidth: int) -> bool:
        return self.available_bandwidth >= bandwidth

    def reserve(
        self,
        allocation: LinkAllocation
    ) -> None:

        if not self.supports(allocation.bandwidth):
            raise ValueError(
                f"O enlace {self.source}-{self.target} "
                "não possui banda suficiente."
            )

        self.allocations.append(allocation)