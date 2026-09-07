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

def create_test_graph() -> NetworkGraph:
    graph = NetworkGraph()

    nodes = {
        name: Node(name)
        for name in [
            "A", "B", "C", "D",
            "E", "F", "G", "H",
            "I", "J", "K", "L"
        ]
    }

    for node in nodes.values():
        graph.add_node(node)

    links = [
        # Caminho 1
        Link(nodes["A"], nodes["B"], 40),
        Link(nodes["B"], nodes["L"], 40),

        # Caminho 2
        Link(nodes["A"], nodes["C"], 80),
        Link(nodes["C"], nodes["D"], 80),
        Link(nodes["D"], nodes["L"], 80),

        # Caminho 3
        Link(nodes["A"], nodes["E"], 160),
        Link(nodes["E"], nodes["F"], 160),
        Link(nodes["F"], nodes["G"], 160),
        Link(nodes["G"], nodes["L"], 160),

        # Caminho 4
        Link(nodes["A"], nodes["H"], 320),
        Link(nodes["H"], nodes["I"], 320),
        Link(nodes["I"], nodes["J"], 320),
        Link(nodes["J"], nodes["K"], 320),
        Link(nodes["K"], nodes["L"], 320),

        # Ligações entre os caminhos
        Link(nodes["B"], nodes["C"], 60),
        Link(nodes["B"], nodes["E"], 90),

        Link(nodes["C"], nodes["E"], 100),
        Link(nodes["C"], nodes["H"], 120),

        Link(nodes["D"], nodes["F"], 110),
        Link(nodes["D"], nodes["G"], 90),

        Link(nodes["E"], nodes["H"], 180),

        Link(nodes["F"], nodes["I"], 200),

        Link(nodes["G"], nodes["J"], 220),
    ]

    for link in links:
        graph.add_link(link)

    return graph