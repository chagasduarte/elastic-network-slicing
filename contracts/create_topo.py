from domain.network_graph import NetworkGraph
from domain.link import Link
from domain.node import Node
from contracts.create_nodes import create_nodes

def create_topo() -> NetworkGraph:
    graph = NetworkGraph()

    nodes = {
        "A": Node("A"),
        "B": Node("B"),
        "C": Node("C"),
        "D": Node("D"),
        "E": Node("E"),
        "F": Node("F"),
        "G": Node("G"),
        "H": Node("H"),
    }
    
    graph.add_link(
        Link(
            source = nodes["A"],
            target= nodes["B"],
            capacity=100
        )
    )

    graph.add_link(
        Link(
            source=nodes["B"],
            target=nodes["D"],
            capacity=100
        )
    )

    graph.add_link(
        Link(
            source=nodes["D"],
            target=nodes["E"],
            capacity=100
        )
    )

    graph.add_link(
        Link(
            source=nodes["A"],
            target=nodes["C"],
            capacity=50
        )
    )

    graph.add_link(
        Link(
            source=nodes["C"],
            target=nodes["E"],
            capacity=50
        )
    )

    graph.add_link(
        Link(
            source=nodes["C"],
            target=nodes["G"],
            capacity=100
        )
    )

    return graph;