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

    def add_Node(self, node: Node) -> None:
        self._nodes.add(node)

    def add_Nodes(self, nodes: list[Node]) -> None:
            for node in nodes:
                self._nodes.add(node)

    def add_link(self, link: Link) -> None:
        self._nodes.add(link.source)
        self._nodes.add(link.target)

        self._links.append(link)

    def get_neighbors(
        self,
        node: Node
    ) -> list[tuple[Node, Link]]:

        neighbors = []

        for link in self._links:
            if link.source == node:
                neighbors.append((link.target, link))

            elif link.target == node:
                neighbors.append((link.source, link))

        return neighbors

    def get_links_from_path(
        self,
        path: list[str]
    ) -> list[Link]:

        links: list[Link] = []

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
                link.source.name == source
                and link.target.name == target
            ):
                return link

            if (
                link.source.name == target
                and link.target.name == source
            ):
                return link

        return None

    def get_links(self):
        return self._links;

    def get_node(self, name: str) -> Node | None:
        for node in self._nodes:
            if node.name == name:
                return node

        return None
    