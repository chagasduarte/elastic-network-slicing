from dataclasses import dataclass


@dataclass(frozen=True)
class SliceResult:
    request_id: str
    demand_id: str
    accepted: bool
    path: list[str]
    bandwidth: int