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
    "A": "Viena, Áustria",
    "B": "Bruxelas, Bélgica",
    "C": "Genebra, Suíça",
    "D": "Praga, República Tcheca",
    "E": "Frankfurt, Alemanha",
    "F": "Madri, Espanha",
    "G": "Paris, França",
    "H": "Atenas, Grécia",
    "I": "Zagreb, Croácia",
    "J": "Budapeste, Hungria",
    "K": "Dublin, Irlanda",
    "L": "Tel Aviv, Israel",
    "M": "Milão, Itália",
    "N": "Luxemburgo",
    "O": "Amsterdã, Países Baixos",
    "P": "Nova York, EUA",
    "Q": "Poznań, Polônia",
    "R": "Lisboa, Portugal",
    "S": "Estocolmo, Suécia",
    "T": "Liubliana, Eslovênia",
    "U": "Bratislava, Eslováquia",
    "V": "Londres, Reino Unido",
}

ORIGINAL_NODE_NAMES = {
    "A": "at1.at",
    "B": "be1.be",
    "C": "ch1.ch",
    "D": "cz1.cz",
    "E": "de1.de",
    "F": "es1.es",
    "G": "fr1.fr",
    "H": "gr1.gr",
    "I": "hr1.hr",
    "J": "hu1.hu",
    "K": "ie1.ie",
    "L": "il1.il",
    "M": "it1.it",
    "N": "lu1.lu",
    "O": "nl1.nl",
    "P": "ny1.ny",
    "Q": "pl1.pl",
    "R": "pt1.pt",
    "S": "se1.se",
    "T": "si1.si",
    "U": "sk1.sk",
    "V": "uk1.uk",
}


NODE_COORDINATES = {
    "A": (16.3729, 48.2091),
    "B": (4.3518, 50.8469),
    "C": (6.1399, 46.2038),
    "D": (14.4423, 50.0785),
    "E": (8.6842, 50.1122),
    "F": (-3.7033, 40.4167),
    "G": (2.351, 48.8566),
    "H": (23.5808, 37.9778),
    "I": (15.9644, 45.8071),
    "J": (19.0936, 47.4976),
    "K": (-6.2573, 53.3416),
    "L": (34.8097, 32.0714),
    "M": (9.19, 45.4642),
    "N": (6.1296, 49.6112),
    "O": (4.9407, 52.3236),
    "P": (-73.94384, 40.6698),
    "Q": (16.8874, 52.3963),
    "R": (-9.1363, 38.7073),
    "S": (17.8742, 59.3617),
    "T": (14.5148, 46.0574),
    "U": (17.1297, 48.1531),
    "V": (-0.1264, 51.5086),
}

# A instância da SNDlib lista capacidade pré-instalada 0 e um módulo
# instalável de 40000 Mbit/s em cada enlace.
DEFAULT_LINK_CAPACITY_MBPS = 40000


def create_geant_graph(
    link_capacity: int = DEFAULT_LINK_CAPACITY_MBPS
) -> NetworkGraph:
    """
    Cria a topologia GEANT da SNDlib: 22 nós e 36 enlaces.

    Como o simulador usa Link com capacidade fixa, por padrão é materializado
    um módulo de 40000 Mbit/s por enlace, valor presente na instância SNDlib.
    """
    if link_capacity <= 0:
        raise ValueError("link_capacity deve ser maior que zero.")

    graph = NetworkGraph()

    nodes = {name: Node(name) for name in NODE_LOCATIONS}

    for node in nodes.values():
        graph.add_node(node)

    links = [
        Link(nodes["A"], nodes["C"], link_capacity),
        Link(nodes["A"], nodes["E"], link_capacity),
        Link(nodes["A"], nodes["J"], link_capacity),
        Link(nodes["A"], nodes["P"], link_capacity),
        Link(nodes["A"], nodes["T"], link_capacity),

        Link(nodes["B"], nodes["G"], link_capacity),
        Link(nodes["B"], nodes["N"], link_capacity),
        Link(nodes["B"], nodes["O"], link_capacity),

        Link(nodes["C"], nodes["G"], link_capacity),
        Link(nodes["C"], nodes["M"], link_capacity),

        Link(nodes["D"], nodes["E"], link_capacity),
        Link(nodes["D"], nodes["Q"], link_capacity),
        Link(nodes["D"], nodes["U"], link_capacity),

        Link(nodes["E"], nodes["G"], link_capacity),
        Link(nodes["E"], nodes["H"], link_capacity),
        Link(nodes["E"], nodes["K"], link_capacity),
        Link(nodes["E"], nodes["M"], link_capacity),
        Link(nodes["E"], nodes["O"], link_capacity),
        Link(nodes["E"], nodes["S"], link_capacity),

        Link(nodes["F"], nodes["G"], link_capacity),
        Link(nodes["F"], nodes["M"], link_capacity),
        Link(nodes["F"], nodes["R"], link_capacity),

        Link(nodes["G"], nodes["N"], link_capacity),
        Link(nodes["G"], nodes["V"], link_capacity),

        Link(nodes["H"], nodes["M"], link_capacity),

        Link(nodes["I"], nodes["J"], link_capacity),
        Link(nodes["I"], nodes["T"], link_capacity),

        Link(nodes["J"], nodes["U"], link_capacity),

        Link(nodes["K"], nodes["V"], link_capacity),

        Link(nodes["L"], nodes["M"], link_capacity),
        Link(nodes["L"], nodes["O"], link_capacity),

        Link(nodes["O"], nodes["V"], link_capacity),

        Link(nodes["P"], nodes["V"], link_capacity),

        Link(nodes["Q"], nodes["S"], link_capacity),

        Link(nodes["R"], nodes["V"], link_capacity),

        Link(nodes["S"], nodes["V"], link_capacity),
    ]

    for link in links:
        graph.add_link(link)

    return graph
