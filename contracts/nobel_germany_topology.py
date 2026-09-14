"""
Topologia para o simulador do TCC.

Os nós foram padronizados como A, B, C... para manter compatibilidade
com a main.py e com as demais topologias do projeto.

Estrutura esperada pelo projeto:
    from domain.network_graph import NetworkGraph
    from domain.link import Link
    from domain.node import Node

A conectividade foi transcrita de instâncias públicas da SNDlib.
Veja README_TOPOLOGIAS.md para as decisões de capacidade usadas na adaptação
para a classe Link do simulador.
"""

from domain.network_graph import NetworkGraph
from domain.link import Link
from domain.node import Node


NODE_LOCATIONS = {
    "A": "Hannover, Alemanha",
    "B": "Frankfurt, Alemanha",
    "C": "Hamburgo, Alemanha",
    "D": "Norden, Alemanha",
    "E": "Bremen, Alemanha",
    "F": "Berlim, Alemanha",
    "G": "Munique, Alemanha",
    "H": "Ulm, Alemanha",
    "I": "Nuremberg, Alemanha",
    "J": "Stuttgart, Alemanha",
    "K": "Karlsruhe, Alemanha",
    "L": "Mannheim, Alemanha",
    "M": "Essen, Alemanha",
    "N": "Dortmund, Alemanha",
    "O": "Düsseldorf, Alemanha",
    "P": "Colônia, Alemanha",
    "Q": "Leipzig, Alemanha",
}

ORIGINAL_NODE_NAMES = {
    "A": "Hannover",
    "B": "Frankfurt",
    "C": "Hamburg",
    "D": "Norden",
    "E": "Bremen",
    "F": "Berlin",
    "G": "Muenchen",
    "H": "Ulm",
    "I": "Nuernberg",
    "J": "Stuttgart",
    "K": "Karlsruhe",
    "L": "Mannheim",
    "M": "Essen",
    "N": "Dortmund",
    "O": "Duesseldorf",
    "P": "Koeln",
    "Q": "Leipzig",
}


NODE_COORDINATES = {
    "A": (9.80, 52.39),
    "B": (8.66, 50.14),
    "C": (10.08, 53.55),
    "D": (7.21, 53.60),
    "E": (8.80, 53.08),
    "F": (13.48, 52.52),
    "G": (11.55, 48.15),
    "H": (9.99, 48.40),
    "I": (11.08, 49.45),
    "J": (9.12, 48.73),
    "K": (8.41, 49.01),
    "L": (8.49, 49.49),
    "M": (7.00, 51.44),
    "N": (7.48, 51.51),
    "O": (6.78, 51.22),
    "P": (7.01, 50.92),
    "Q": (12.38, 51.34),
}

DEFAULT_LINK_CAPACITY_MBPS = 800


def create_nobel_germany_graph(
    link_capacity: int = DEFAULT_LINK_CAPACITY_MBPS
) -> NetworkGraph:
    """
    Cria a topologia Nobel-Germany da SNDlib: 17 nós e 26 enlaces.

    A instância nativa da SNDlib possui capacidade pré-instalada igual a zero
    e opções de capacidade instalável. Como a classe Link do simulador exige
    uma capacidade fixa, esta adaptação materializa uma capacidade por enlace.

    O valor padrão de 800 Mbit/s corresponde ao maior valor de capacidade
    listado entre as opções da instância. Para experimentos normalizados,
    passe outro valor explicitamente.
    """
    if link_capacity <= 0:
        raise ValueError("link_capacity deve ser maior que zero.")

    graph = NetworkGraph()

    nodes = {name: Node(name) for name in NODE_LOCATIONS}

    for node in nodes.values():
        graph.add_node(node)

    links = [
        Link(nodes["F"], nodes["C"], link_capacity),
        Link(nodes["F"], nodes["A"], link_capacity),
        Link(nodes["F"], nodes["Q"], link_capacity),

        Link(nodes["E"], nodes["C"], link_capacity),
        Link(nodes["E"], nodes["A"], link_capacity),
        Link(nodes["E"], nodes["D"], link_capacity),

        Link(nodes["N"], nodes["M"], link_capacity),
        Link(nodes["N"], nodes["A"], link_capacity),
        Link(nodes["N"], nodes["P"], link_capacity),
        Link(nodes["N"], nodes["D"], link_capacity),

        Link(nodes["O"], nodes["M"], link_capacity),
        Link(nodes["O"], nodes["P"], link_capacity),

        Link(nodes["B"], nodes["A"], link_capacity),
        Link(nodes["B"], nodes["P"], link_capacity),
        Link(nodes["B"], nodes["Q"], link_capacity),
        Link(nodes["B"], nodes["L"], link_capacity),
        Link(nodes["B"], nodes["I"], link_capacity),

        Link(nodes["C"], nodes["A"], link_capacity),
        Link(nodes["A"], nodes["Q"], link_capacity),

        Link(nodes["K"], nodes["L"], link_capacity),
        Link(nodes["K"], nodes["J"], link_capacity),

        Link(nodes["Q"], nodes["I"], link_capacity),

        Link(nodes["G"], nodes["I"], link_capacity),
        Link(nodes["G"], nodes["H"], link_capacity),

        Link(nodes["I"], nodes["J"], link_capacity),
        Link(nodes["J"], nodes["H"], link_capacity),
    ]

    for link in links:
        graph.add_link(link)

    return graph
