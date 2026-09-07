from dataclasses import dataclass
from domain.node import Node

@dataclass(frozen=True)
class SliceResult:
    request_id: str
    demand_id: str
    accepted: bool
    path: list[str]
    bandwidth: int