import math

from contracts.link_weight_calculator import LinkWeightCalculator
from domain.link import Link


class PeticWeightCalculator(LinkWeightCalculator):

    def calculate(
        self,
        link: Link,
        bandwidth: int
    ) -> float:

        if not link.supports(bandwidth):
            return math.inf

        return math.exp(
            bandwidth / link.available_bandwidth
        )