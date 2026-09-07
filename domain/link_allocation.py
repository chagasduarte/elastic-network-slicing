from dataclasses import dataclass


@dataclass(frozen=True)
class LinkAllocation:
    request_id: str
    demand_id: str
    bandwidth: int

    def __post_init__(self):
        if self.bandwidth <= 0:
            raise ValueError(
                "A largura de banda alocada deve ser maior que zero."
            )