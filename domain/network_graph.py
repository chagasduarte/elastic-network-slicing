from domain.link import Link
from domain.node import Node
class NetworkGraph:
    def __init__(self):
        self._nodes: set[Node] = set()
        self._links: list[Link] = []
        self._by_name: dict[str, Node] = {}
        # Vizinhos na ordem de inserção dos enlaces, igual à varredura linear.
        self._adjacency: dict[Node, list[tuple[Node, Link]]] = {}
        # Primeiro enlace inserido para cada par de nomes, nos dois sentidos.
        self._link_index: dict[tuple[str, str], Link] = {}

    @property
    def nodes(self) -> set[Node]:
        return self._nodes.copy()

    @property
    def links(self) -> list[Link]:
        return self._links.copy()

    def add_node(self, node: Node) -> None:
        self._nodes.add(node)
        self._by_name.setdefault(node.name, node)

    def add_nodes(self, nodes: list[Node]) -> None:
            for node in nodes:
                self.add_node(node)

    def add_link(self, link: Link) -> None:
        self.add_node(link.source)
        self.add_node(link.target)

        self._links.append(link)
        self._adjacency.setdefault(link.source, []).append((link.target, link))
        if link.target != link.source:
            self._adjacency.setdefault(link.target, []).append((link.source, link))
        self._link_index.setdefault((link.source.name, link.target.name), link)
        self._link_index.setdefault((link.target.name, link.source.name), link)

    def get_neighbors(
        self,
        node: Node
    ) -> list[tuple[Node, Link]]:

        return list(self._adjacency.get(node, ()))

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

        return self._link_index.get((source, target))

    def get_links(self):
        return self._links

    def get_node(self, name: str) -> Node | None:
        return self._by_name.get(name)
