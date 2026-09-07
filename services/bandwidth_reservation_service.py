from domain.link import Link
from domain.link_allocation import LinkAllocation


class BandwidthReservationService:

    def reserve(
        self,
        links: list[Link],
        allocation: LinkAllocation
    ) -> None:

        self._validate(links, allocation)

        for link in links:
            link.reserve(allocation)

    def _validate(
        self,
        links: list[Link],
        allocation: LinkAllocation
    ) -> None:

        for link in links:
            if not link.supports(allocation.demand_id ,allocation.bandwidth):
                raise ValueError(
                    f"O enlace {link.source}-{link.target} "
                    f"não possui {allocation.bandwidth} Mbps disponíveis."
                )