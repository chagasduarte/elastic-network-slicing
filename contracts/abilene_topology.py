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
    "ATLAM5": "Atlanta, Georgia, EUA",
    "ATLAng": "Atlanta, Georgia, EUA",
    "CHINng": "Chicago, Illinois, EUA",
    "DNVRng": "Denver, Colorado, EUA",
    "HSTNng": "Houston, Texas, EUA",
    "IPLSng": "Indianapolis, Indiana, EUA",
    "KSCYng": "Kansas City, EUA",
    "LOSAng": "Los Angeles, California, EUA",
    "NYCMng": "Nova York, New York, EUA",
    "SNVAng": "Sunnyvale, California, EUA",
    "STTLng": "Seattle, Washington, EUA",
    "WASHng": "Washington, DC, EUA",
}

NODE_COORDINATES = {
    "ATLAM5": (-84.3833, 33.75),
    "ATLAng": (-85.50, 34.50),
    "CHINng": (-87.6167, 41.8333),
    "DNVRng": (-105.00, 40.75),
    "HSTNng": (-95.517364, 29.770031),
    "IPLSng": (-86.159535, 39.780622),
    "KSCYng": (-96.596704, 38.961694),
    "LOSAng": (-118.25, 34.05),
    "NYCMng": (-73.9667, 40.7833),
    "SNVAng": (-122.02553, 37.38575),
    "STTLng": (-122.30, 47.60),
    "WASHng": (-77.026842, 38.897303),
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
        Link(nodes["ATLAng"], nodes["ATLAM5"], cap(9920)),
        Link(nodes["HSTNng"], nodes["ATLAng"], cap(9920)),
        Link(nodes["IPLSng"], nodes["ATLAng"], cap(2480)),
        Link(nodes["WASHng"], nodes["ATLAng"], cap(9920)),
        Link(nodes["IPLSng"], nodes["CHINng"], cap(9920)),
        Link(nodes["NYCMng"], nodes["CHINng"], cap(9920)),
        Link(nodes["KSCYng"], nodes["DNVRng"], cap(9920)),
        Link(nodes["SNVAng"], nodes["DNVRng"], cap(9920)),
        Link(nodes["STTLng"], nodes["DNVRng"], cap(9920)),
        Link(nodes["KSCYng"], nodes["HSTNng"], cap(9920)),
        Link(nodes["LOSAng"], nodes["HSTNng"], cap(9920)),
        Link(nodes["KSCYng"], nodes["IPLSng"], cap(9920)),
        Link(nodes["SNVAng"], nodes["LOSAng"], cap(9920)),
        Link(nodes["WASHng"], nodes["NYCMng"], cap(9920)),
        Link(nodes["STTLng"], nodes["SNVAng"], cap(9920)),
    ]

    for link in links:
        graph.add_link(link)

    return graph
