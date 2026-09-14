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
    "at1.at": "Viena, Áustria",
    "be1.be": "Bruxelas, Bélgica",
    "ch1.ch": "Genebra, Suíça",
    "cz1.cz": "Praga, República Tcheca",
    "de1.de": "Frankfurt, Alemanha",
    "es1.es": "Madri, Espanha",
    "fr1.fr": "Paris, França",
    "gr1.gr": "Atenas, Grécia",
    "hr1.hr": "Zagreb, Croácia",
    "hu1.hu": "Budapeste, Hungria",
    "ie1.ie": "Dublin, Irlanda",
    "il1.il": "Tel Aviv, Israel",
    "it1.it": "Milão, Itália",
    "lu1.lu": "Luxemburgo",
    "nl1.nl": "Amsterdã, Países Baixos",
    "ny1.ny": "Nova York, EUA",
    "pl1.pl": "Poznań, Polônia",
    "pt1.pt": "Lisboa, Portugal",
    "se1.se": "Estocolmo, Suécia",
    "si1.si": "Liubliana, Eslovênia",
    "sk1.sk": "Bratislava, Eslováquia",
    "uk1.uk": "Londres, Reino Unido",
}

NODE_COORDINATES = {
    "at1.at": (16.3729, 48.2091),
    "be1.be": (4.3518, 50.8469),
    "ch1.ch": (6.1399, 46.2038),
    "cz1.cz": (14.4423, 50.0785),
    "de1.de": (8.6842, 50.1122),
    "es1.es": (-3.7033, 40.4167),
    "fr1.fr": (2.351, 48.8566),
    "gr1.gr": (23.5808, 37.9778),
    "hr1.hr": (15.9644, 45.8071),
    "hu1.hu": (19.0936, 47.4976),
    "ie1.ie": (-6.2573, 53.3416),
    "il1.il": (34.8097, 32.0714),
    "it1.it": (9.19, 45.4642),
    "lu1.lu": (6.1296, 49.6112),
    "nl1.nl": (4.9407, 52.3236),
    "ny1.ny": (-73.94384, 40.6698),
    "pl1.pl": (16.8874, 52.3963),
    "pt1.pt": (-9.1363, 38.7073),
    "se1.se": (17.8742, 59.3617),
    "si1.si": (14.5148, 46.0574),
    "sk1.sk": (17.1297, 48.1531),
    "uk1.uk": (-0.1264, 51.5086),
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
        Link(nodes["at1.at"], nodes["ch1.ch"], link_capacity),
        Link(nodes["at1.at"], nodes["de1.de"], link_capacity),
        Link(nodes["at1.at"], nodes["hu1.hu"], link_capacity),
        Link(nodes["at1.at"], nodes["ny1.ny"], link_capacity),
        Link(nodes["at1.at"], nodes["si1.si"], link_capacity),

        Link(nodes["be1.be"], nodes["fr1.fr"], link_capacity),
        Link(nodes["be1.be"], nodes["lu1.lu"], link_capacity),
        Link(nodes["be1.be"], nodes["nl1.nl"], link_capacity),

        Link(nodes["ch1.ch"], nodes["fr1.fr"], link_capacity),
        Link(nodes["ch1.ch"], nodes["it1.it"], link_capacity),

        Link(nodes["cz1.cz"], nodes["de1.de"], link_capacity),
        Link(nodes["cz1.cz"], nodes["pl1.pl"], link_capacity),
        Link(nodes["cz1.cz"], nodes["sk1.sk"], link_capacity),

        Link(nodes["de1.de"], nodes["fr1.fr"], link_capacity),
        Link(nodes["de1.de"], nodes["gr1.gr"], link_capacity),
        Link(nodes["de1.de"], nodes["ie1.ie"], link_capacity),
        Link(nodes["de1.de"], nodes["it1.it"], link_capacity),
        Link(nodes["de1.de"], nodes["nl1.nl"], link_capacity),
        Link(nodes["de1.de"], nodes["se1.se"], link_capacity),

        Link(nodes["es1.es"], nodes["fr1.fr"], link_capacity),
        Link(nodes["es1.es"], nodes["it1.it"], link_capacity),
        Link(nodes["es1.es"], nodes["pt1.pt"], link_capacity),

        Link(nodes["fr1.fr"], nodes["lu1.lu"], link_capacity),
        Link(nodes["fr1.fr"], nodes["uk1.uk"], link_capacity),

        Link(nodes["gr1.gr"], nodes["it1.it"], link_capacity),

        Link(nodes["hr1.hr"], nodes["hu1.hu"], link_capacity),
        Link(nodes["hr1.hr"], nodes["si1.si"], link_capacity),

        Link(nodes["hu1.hu"], nodes["sk1.sk"], link_capacity),

        Link(nodes["ie1.ie"], nodes["uk1.uk"], link_capacity),

        Link(nodes["il1.il"], nodes["it1.it"], link_capacity),
        Link(nodes["il1.il"], nodes["nl1.nl"], link_capacity),

        Link(nodes["nl1.nl"], nodes["uk1.uk"], link_capacity),

        Link(nodes["ny1.ny"], nodes["uk1.uk"], link_capacity),

        Link(nodes["pl1.pl"], nodes["se1.se"], link_capacity),

        Link(nodes["pt1.pt"], nodes["uk1.uk"], link_capacity),

        Link(nodes["se1.se"], nodes["uk1.uk"], link_capacity),
    ]

    for link in links:
        graph.add_link(link)

    return graph
