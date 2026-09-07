from abc import ABC, abstractmethod

from domain.link import Link


class LinkWeightCalculator(ABC):

    @abstractmethod
    def calculate(
        self,
        link: Link,
        bandwidth: int
    ) -> float:
        pass