from domain.network_graph import NetworkGraph
from domain.link import Link
from domain.node import Node

def create_topo() -> NetworkGraph:
    graph = NetworkGraph()

    
    graph.add_link(
        Link(
            source = Node("a"),
            target= Node("B"),
            capacity=100
        )
    )

    graph.add_link(
        Link(
            source="B",
            target="D",
            capacity=100
        )
    )

    graph.add_link(
        Link(
            source="D",
            target="E",
            capacity=100
        )
    )

    graph.add_link(
        Link(
            source="A",
            target="C",
            capacity=50
        )
    )

    graph.add_link(
        Link(
            source="C",
            target="E",
            capacity=50
        )
    )

    return graph;