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
    "A": "Atlanta, Georgia, EUA",
    "B": "Atlanta, Georgia, EUA",
    "C": "Chicago, Illinois, EUA",
    "D": "Denver, Colorado, EUA",
    "E": "Houston, Texas, EUA",
    "F": "Indianapolis, Indiana, EUA",
    "G": "Kansas City, EUA",
    "H": "Los Angeles, California, EUA",
    "I": "Nova York, New York, EUA",
    "J": "Sunnyvale, California, EUA",
    "K": "Seattle, Washington, EUA",
    "L": "Washington, DC, EUA",
}

ORIGINAL_NODE_NAMES = {
    "A": "ATLAM5",
    "B": "ATLAng",
    "C": "CHINng",
    "D": "DNVRng",
    "E": "HSTNng",
    "F": "IPLSng",
    "G": "KSCYng",
    "H": "LOSAng",
    "I": "NYCMng",
    "J": "SNVAng",
    "K": "STTLng",
    "L": "WASHng",
}


NODE_COORDINATES = {
    "A": (-84.3833, 33.75),
    "B": (-85.50, 34.50),
    "C": (-87.6167, 41.8333),
    "D": (-105.00, 40.75),
    "E": (-95.517364, 29.770031),
    "F": (-86.159535, 39.780622),
    "G": (-96.596704, 38.961694),
    "H": (-118.25, 34.05),
    "I": (-73.9667, 40.7833),
    "J": (-122.02553, 37.38575),
    "K": (-122.30, 47.60),
    "L": (-77.026842, 38.897303),
}


def create_abilene_graph(capacity_scale: float = 1.0) -> NetworkGraph:
    """
    Cria a topologia Abilene da SNDlib.

    Capacidades:
        - usa a capacidade pré-instalada indicada pela SNDlib;
        - 13 enlaces possuem 9920 Mbit/s;
        - 1 enlace possui 2480 Mbit/s;
        - ATLAM5 <-> ATLAng possui 9920 Mbit/s.

    capacity_scale permite reduzir/aumentar todas as capacidades mantendo
    a proporção original. Para reproduzir os valores da SNDlib, use 1.0.
    """
    if capacity_scale <= 0:
        raise ValueError("capacity_scale deve ser maior que zero.")

    graph = NetworkGraph()

    nodes = {name: Node(name) for name in NODE_LOCATIONS}

    for node in nodes.values():
        graph.add_node(node)

    def cap(value: int) -> int:
        return max(1, int(round(value * capacity_scale)))

    links = [
        Link(nodes["B"], nodes["A"], cap(9920)),
        Link(nodes["E"], nodes["B"], cap(9920)),
        Link(nodes["F"], nodes["B"], cap(2480)),
        Link(nodes["L"], nodes["B"], cap(9920)),
        Link(nodes["F"], nodes["C"], cap(9920)),
        Link(nodes["I"], nodes["C"], cap(9920)),
        Link(nodes["G"], nodes["D"], cap(9920)),
        Link(nodes["J"], nodes["D"], cap(9920)),
        Link(nodes["K"], nodes["D"], cap(9920)),
        Link(nodes["G"], nodes["E"], cap(9920)),
        Link(nodes["H"], nodes["E"], cap(9920)),
        Link(nodes["G"], nodes["F"], cap(9920)),
        Link(nodes["J"], nodes["H"], cap(9920)),
        Link(nodes["L"], nodes["I"], cap(9920)),
        Link(nodes["K"], nodes["J"], cap(9920)),
    ]

    for link in links:
        graph.add_link(link)

    return graph
