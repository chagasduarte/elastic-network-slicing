import math

from contracts.link_weight_calculator import LinkWeightCalculator
from domain.link import Link
from domain.slice_demand import SliceDemand


class PeticWeightCalculator(LinkWeightCalculator):

    def calculate(
        self,
        link: Link,
        demand: SliceDemand
    ) -> float:

        available = link.available_bandwidth_at(
            demand.id
        )

        if available < demand.bandwidth:
            return math.inf

        return math.exp(
            demand.bandwidth / available
        )