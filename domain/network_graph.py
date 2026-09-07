from domain.link import Link
from domain.node import Node
class NetworkGraph:
    def __init__(self):
        self._nodes: set[Node] = set()
        self._links: list[Link] = []

    @property
    def nodes(self) -> set[Node]:
        return self._nodes.copy()

    @property
    def links(self) -> list[Link]:
        return self._links.copy()

    def add_link(self, link: Link) -> None:
        self._nodes.add(link.source)
        self._nodes.add(link.target)

        self._links.append(link)

    def get_neighbors(
            
        self,
        node: str
    ) -> list[tuple[str, Link]]:

        neighbors = []

        for link in self._links:

            if link.source == node:
                neighbors.append(
                    (link.target, link)
                )

            elif link.target == node:
                neighbors.append(
                    (link.source, link)
                )

        return neighbors

    def get_links_from_path(
        self,
        path: list[str]
    ) -> list[Link]:

        links = []

        for index in range(len(path) - 1):
            source = path[index]
            target = path[index + 1]

            link = self.get_link(
                source,
                target
            )

            if link is None:
                raise ValueError(
                    f"Enlace {source}-{target} não encontrado."
                )

            links.append(link)

        return links

    def get_link(
        self,
        source: str,
        target: str
    ) -> Link | None:

        for link in self._links:
            if (
                link.source == source
                and link.target == target
            ) or (
                link.source == target
                and link.target == source
            ):
                return link

        return None

    def get_links(self):
        return self._links;
    