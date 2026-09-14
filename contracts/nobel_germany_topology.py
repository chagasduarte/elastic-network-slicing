"""
Topologia para o simulador do TCC.

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
    "Hannover": "Hannover, Alemanha",
    "Frankfurt": "Frankfurt, Alemanha",
    "Hamburg": "Hamburgo, Alemanha",
    "Norden": "Norden, Alemanha",
    "Bremen": "Bremen, Alemanha",
    "Berlin": "Berlim, Alemanha",
    "Muenchen": "Munique, Alemanha",
    "Ulm": "Ulm, Alemanha",
    "Nuernberg": "Nuremberg, Alemanha",
    "Stuttgart": "Stuttgart, Alemanha",
    "Karlsruhe": "Karlsruhe, Alemanha",
    "Mannheim": "Mannheim, Alemanha",
    "Essen": "Essen, Alemanha",
    "Dortmund": "Dortmund, Alemanha",
    "Duesseldorf": "Düsseldorf, Alemanha",
    "Koeln": "Colônia, Alemanha",
    "Leipzig": "Leipzig, Alemanha",
}

NODE_COORDINATES = {
    "Hannover": (9.80, 52.39),
    "Frankfurt": (8.66, 50.14),
    "Hamburg": (10.08, 53.55),
    "Norden": (7.21, 53.60),
    "Bremen": (8.80, 53.08),
    "Berlin": (13.48, 52.52),
    "Muenchen": (11.55, 48.15),
    "Ulm": (9.99, 48.40),
    "Nuernberg": (11.08, 49.45),
    "Stuttgart": (9.12, 48.73),
    "Karlsruhe": (8.41, 49.01),
    "Mannheim": (8.49, 49.49),
    "Essen": (7.00, 51.44),
    "Dortmund": (7.48, 51.51),
    "Duesseldorf": (6.78, 51.22),
    "Koeln": (7.01, 50.92),
    "Leipzig": (12.38, 51.34),
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
        Link(nodes["Berlin"], nodes["Hamburg"], link_capacity),
        Link(nodes["Berlin"], nodes["Hannover"], link_capacity),
        Link(nodes["Berlin"], nodes["Leipzig"], link_capacity),

        Link(nodes["Bremen"], nodes["Hamburg"], link_capacity),
        Link(nodes["Bremen"], nodes["Hannover"], link_capacity),
        Link(nodes["Bremen"], nodes["Norden"], link_capacity),

        Link(nodes["Dortmund"], nodes["Essen"], link_capacity),
        Link(nodes["Dortmund"], nodes["Hannover"], link_capacity),
        Link(nodes["Dortmund"], nodes["Koeln"], link_capacity),
        Link(nodes["Dortmund"], nodes["Norden"], link_capacity),

        Link(nodes["Duesseldorf"], nodes["Essen"], link_capacity),
        Link(nodes["Duesseldorf"], nodes["Koeln"], link_capacity),

        Link(nodes["Frankfurt"], nodes["Hannover"], link_capacity),
        Link(nodes["Frankfurt"], nodes["Koeln"], link_capacity),
        Link(nodes["Frankfurt"], nodes["Leipzig"], link_capacity),
        Link(nodes["Frankfurt"], nodes["Mannheim"], link_capacity),
        Link(nodes["Frankfurt"], nodes["Nuernberg"], link_capacity),

        Link(nodes["Hamburg"], nodes["Hannover"], link_capacity),
        Link(nodes["Hannover"], nodes["Leipzig"], link_capacity),

        Link(nodes["Karlsruhe"], nodes["Mannheim"], link_capacity),
        Link(nodes["Karlsruhe"], nodes["Stuttgart"], link_capacity),

        Link(nodes["Leipzig"], nodes["Nuernberg"], link_capacity),

        Link(nodes["Muenchen"], nodes["Nuernberg"], link_capacity),
        Link(nodes["Muenchen"], nodes["Ulm"], link_capacity),

        Link(nodes["Nuernberg"], nodes["Stuttgart"], link_capacity),
        Link(nodes["Stuttgart"], nodes["Ulm"], link_capacity),
    ]

    for link in links:
        graph.add_link(link)

    return graph
