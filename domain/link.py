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

    def allocated_bandwidth_at(
        self,
        demand_id: str
    ) -> int:
        return sum(
            allocation.bandwidth
            for allocation in self.allocations
            if allocation.demand_id == demand_id
        )

    def available_bandwidth_at(
        self,
        demand_id: str
    ) -> int:
        return (
            self.capacity
            - self.allocated_bandwidth_at(demand_id)
        )

    def supports(
        self,
        demand_id: str,
        bandwidth: int
    ) -> bool:
        return (
            self.available_bandwidth_at(demand_id)
            >= bandwidth
        )

    def reserve(
        self,
        allocation: LinkAllocation
    ) -> None:
        if not self.supports(
            allocation.demand_id,
            allocation.bandwidth
        ):
            raise ValueError(
                f"O enlace "
                f"{self.source.id}-{self.target.id} "
                "não possui banda suficiente."
            )

        self.allocations.append(allocation)