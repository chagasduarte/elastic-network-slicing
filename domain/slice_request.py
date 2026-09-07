from dataclasses import dataclass
from domain.slice_demand import SliceDemand


@dataclass(frozen=True)
class SliceRequest:
    id: str
    source: str
    destination: str
    demands: list[SliceDemand]

    def demand_at(self, period_id: str) -> SliceDemand:
        for demand in self.demands:
            if demand.id == period_id:
                return demand
            
        raise ValueError(
            f"Não existe demanda para o período {period_id}."
        )