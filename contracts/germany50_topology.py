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
    "A": "Aachen, Alemanha",
    "B": "Augsburg, Alemanha",
    "C": "Bayreuth, Alemanha",
    "D": "Berlim, Alemanha",
    "E": "Bielefeld, Alemanha",
    "F": "Braunschweig, Alemanha",
    "G": "Bremen, Alemanha",
    "H": "Bremerhaven, Alemanha",
    "I": "Chemnitz, Alemanha",
    "J": "Darmstadt, Alemanha",
    "K": "Dortmund, Alemanha",
    "L": "Dresden, Alemanha",
    "M": "Düsseldorf, Alemanha",
    "N": "Erfurt, Alemanha",
    "O": "Essen, Alemanha",
    "P": "Flensburg, Alemanha",
    "Q": "Frankfurt, Alemanha",
    "R": "Freiburg, Alemanha",
    "S": "Fulda, Alemanha",
    "T": "Giessen, Alemanha",
    "U": "Greifswald, Alemanha",
    "V": "Hamburgo, Alemanha",
    "W": "Hannover, Alemanha",
    "X": "Kaiserslautern, Alemanha",
    "Y": "Karlsruhe, Alemanha",
    "Z": "Kassel, Alemanha",
    "AA": "Kempten, Alemanha",
    "AB": "Kiel, Alemanha",
    "AC": "Koblenz, Alemanha",
    "AD": "Colônia, Alemanha",
    "AE": "Konstanz, Alemanha",
    "AF": "Leipzig, Alemanha",
    "AG": "Magdeburg, Alemanha",
    "AH": "Mannheim, Alemanha",
    "AI": "Munique, Alemanha",
    "AJ": "Münster, Alemanha",
    "AK": "Norden, Alemanha",
    "AL": "Nuremberg, Alemanha",
    "AM": "Oldenburg, Alemanha",
    "AN": "Osnabrück, Alemanha",
    "AO": "Passau, Alemanha",
    "AP": "Regensburg, Alemanha",
    "AQ": "Saarbrücken, Alemanha",
    "AR": "Schwerin, Alemanha",
    "AS": "Siegen, Alemanha",
    "AT": "Stuttgart, Alemanha",
    "AU": "Trier, Alemanha",
    "AV": "Ulm, Alemanha",
    "AW": "Wesel, Alemanha",
    "AX": "Würzburg, Alemanha",
}

ORIGINAL_NODE_NAMES = {
    "A": "Aachen",
    "B": "Augsburg",
    "C": "Bayreuth",
    "D": "Berlin",
    "E": "Bielefeld",
    "F": "Braunschweig",
    "G": "Bremen",
    "H": "Bremerhaven",
    "I": "Chemnitz",
    "J": "Darmstadt",
    "K": "Dortmund",
    "L": "Dresden",
    "M": "Duesseldorf",
    "N": "Erfurt",
    "O": "Essen",
    "P": "Flensburg",
    "Q": "Frankfurt",
    "R": "Freiburg",
    "S": "Fulda",
    "T": "Giessen",
    "U": "Greifswald",
    "V": "Hamburg",
    "W": "Hannover",
    "X": "Kaiserslautern",
    "Y": "Karlsruhe",
    "Z": "Kassel",
    "AA": "Kempten",
    "AB": "Kiel",
    "AC": "Koblenz",
    "AD": "Koeln",
    "AE": "Konstanz",
    "AF": "Leipzig",
    "AG": "Magdeburg",
    "AH": "Mannheim",
    "AI": "Muenchen",
    "AJ": "Muenster",
    "AK": "Norden",
    "AL": "Nuernberg",
    "AM": "Oldenburg",
    "AN": "Osnabrueck",
    "AO": "Passau",
    "AP": "Regensburg",
    "AQ": "Saarbruecken",
    "AR": "Schwerin",
    "AS": "Siegen",
    "AT": "Stuttgart",
    "AU": "Trier",
    "AV": "Ulm",
    "AW": "Wesel",
    "AX": "Wuerzburg",
}


NODE_COORDINATES = {
    "A": (6.04, 50.76),
    "B": (10.90, 48.33),
    "C": (11.59, 49.93),
    "D": (13.39, 52.52),
    "E": (8.50, 52.04),
    "F": (10.55, 52.28),
    "G": (8.85, 53.11),
    "H": (8.58, 53.54),
    "I": (12.93, 50.84),
    "J": (8.65, 49.89),
    "K": (7.45, 51.51),
    "L": (13.73, 51.03),
    "M": (6.77, 51.25),
    "N": (11.04, 50.98),
    "O": (7.02, 51.46),
    "P": (9.45, 54.77),
    "Q": (8.71, 50.12),
    "R": (7.80, 47.98),
    "S": (9.69, 50.56),
    "T": (8.67, 50.57),
    "U": (13.40, 54.09),
    "V": (9.99, 53.57),
    "W": (9.72, 52.38),
    "X": (7.75, 49.43),
    "Y": (8.41, 49.01),
    "Z": (9.51, 51.32),
    "AA": (10.32, 47.72),
    "AB": (10.12, 54.34),
    "AC": (7.52, 50.40),
    "AD": (6.87, 50.94),
    "AE": (9.18, 47.66),
    "AF": (12.38, 51.34),
    "AG": (11.64, 52.14),
    "AH": (8.49, 49.49),
    "AI": (11.57, 48.15),
    "AJ": (7.60, 51.97),
    "AK": (7.21, 53.60),
    "AL": (11.03, 49.57),
    "AM": (8.21, 53.11),
    "AN": (8.03, 52.28),
    "AO": (13.46, 48.57),
    "AP": (12.09, 49.00),
    "AQ": (7.03, 49.23),
    "AR": (11.45, 53.55),
    "AS": (8.03, 50.91),
    "AT": (9.10, 48.74),
    "AU": (6.68, 49.75),
    "AV": (9.99, 48.40),
    "AW": (6.37, 51.39),
    "AX": (9.97, 49.78),
}

BASE_MODULE_CAPACITY_MBPS = 40
DEFAULT_MODULES_PER_LINK = 20


def create_germany50_graph(
    modules_per_link: int = DEFAULT_MODULES_PER_LINK
) -> NetworkGraph:
    """
    Cria a topologia Germany50 da SNDlib: 50 nós e 88 enlaces.

    A instância nativa possui capacidade pré-instalada 0 e lista um módulo
    adicional de 40 Mbit/s por enlace. Como Link exige capacidade fixa, esta
    adaptação materializa:

        capacidade = 40 * modules_per_link

    O padrão é 20 módulos, ou 800 Mbit/s por enlace. Isso é uma decisão
    experimental do simulador, não deve ser descrito no TCC como capacidade
    física originalmente instalada na rede.
    """
    if modules_per_link <= 0:
        raise ValueError("modules_per_link deve ser maior que zero.")

    link_capacity = BASE_MODULE_CAPACITY_MBPS * modules_per_link

    graph = NetworkGraph()

    nodes = {name: Node(name) for name in NODE_LOCATIONS}

    for node in nodes.values():
        graph.add_node(node)

    links = [
        Link(nodes["M"], nodes["O"], link_capacity),
        Link(nodes["K"], nodes["O"], link_capacity),
        Link(nodes["AW"], nodes["O"], link_capacity),
        Link(nodes["AD"], nodes["M"], link_capacity),
        Link(nodes["A"], nodes["AD"], link_capacity),
        Link(nodes["AC"], nodes["AD"], link_capacity),
        Link(nodes["AJ"], nodes["K"], link_capacity),
        Link(nodes["AS"], nodes["K"], link_capacity),
        Link(nodes["Z"], nodes["K"], link_capacity),
        Link(nodes["AW"], nodes["A"], link_capacity),
        Link(nodes["AU"], nodes["A"], link_capacity),
        Link(nodes["E"], nodes["AJ"], link_capacity),
        Link(nodes["AN"], nodes["AJ"], link_capacity),
        Link(nodes["AS"], nodes["AC"], link_capacity),
        Link(nodes["Q"], nodes["AC"], link_capacity),
        Link(nodes["X"], nodes["AC"], link_capacity),
        Link(nodes["AU"], nodes["AC"], link_capacity),
        Link(nodes["E"], nodes["AS"], link_capacity),
        Link(nodes["T"], nodes["AS"], link_capacity),
        Link(nodes["AM"], nodes["AW"], link_capacity),
        Link(nodes["AK"], nodes["AW"], link_capacity),

        Link(nodes["AF"], nodes["D"], link_capacity),
        Link(nodes["L"], nodes["D"], link_capacity),
        Link(nodes["AR"], nodes["D"], link_capacity),
        Link(nodes["AG"], nodes["D"], link_capacity),
        Link(nodes["U"], nodes["D"], link_capacity),

        Link(nodes["L"], nodes["AF"], link_capacity),
        Link(nodes["N"], nodes["AF"], link_capacity),
        Link(nodes["AG"], nodes["AF"], link_capacity),
        Link(nodes["C"], nodes["AF"], link_capacity),

        Link(nodes["N"], nodes["L"], link_capacity),
        Link(nodes["I"], nodes["L"], link_capacity),
        Link(nodes["I"], nodes["N"], link_capacity),
        Link(nodes["Z"], nodes["N"], link_capacity),
        Link(nodes["AX"], nodes["N"], link_capacity),
        Link(nodes["C"], nodes["I"], link_capacity),

        Link(nodes["AG"], nodes["AR"], link_capacity),
        Link(nodes["U"], nodes["AR"], link_capacity),
        Link(nodes["V"], nodes["AR"], link_capacity),
        Link(nodes["AB"], nodes["AR"], link_capacity),

        Link(nodes["F"], nodes["AG"], link_capacity),

        Link(nodes["AB"], nodes["V"], link_capacity),
        Link(nodes["W"], nodes["V"], link_capacity),
        Link(nodes["F"], nodes["V"], link_capacity),

        Link(nodes["AM"], nodes["G"], link_capacity),
        Link(nodes["H"], nodes["G"], link_capacity),
        Link(nodes["W"], nodes["G"], link_capacity),

        Link(nodes["P"], nodes["AB"], link_capacity),
        Link(nodes["AK"], nodes["AM"], link_capacity),
        Link(nodes["AN"], nodes["AM"], link_capacity),
        Link(nodes["H"], nodes["P"], link_capacity),

        Link(nodes["E"], nodes["W"], link_capacity),
        Link(nodes["F"], nodes["W"], link_capacity),
        Link(nodes["AN"], nodes["W"], link_capacity),
        Link(nodes["F"], nodes["E"], link_capacity),
        Link(nodes["Z"], nodes["F"], link_capacity),

        Link(nodes["T"], nodes["Z"], link_capacity),
        Link(nodes["S"], nodes["Z"], link_capacity),

        Link(nodes["J"], nodes["Q"], link_capacity),
        Link(nodes["T"], nodes["Q"], link_capacity),
        Link(nodes["S"], nodes["Q"], link_capacity),

        Link(nodes["AH"], nodes["J"], link_capacity),
        Link(nodes["X"], nodes["J"], link_capacity),

        Link(nodes["Y"], nodes["AH"], link_capacity),
        Link(nodes["AQ"], nodes["X"], link_capacity),
        Link(nodes["Y"], nodes["X"], link_capacity),
        Link(nodes["S"], nodes["T"], link_capacity),
        Link(nodes["AQ"], nodes["AU"], link_capacity),
        Link(nodes["AX"], nodes["S"], link_capacity),

        Link(nodes["Y"], nodes["AQ"], link_capacity),
        Link(nodes["Y"], nodes["AT"], link_capacity),
        Link(nodes["AV"], nodes["AT"], link_capacity),
        Link(nodes["AE"], nodes["AT"], link_capacity),
        Link(nodes["AX"], nodes["AT"], link_capacity),
        Link(nodes["R"], nodes["Y"], link_capacity),

        Link(nodes["B"], nodes["AV"], link_capacity),
        Link(nodes["R"], nodes["AE"], link_capacity),
        Link(nodes["AA"], nodes["AE"], link_capacity),

        Link(nodes["B"], nodes["AI"], link_capacity),
        Link(nodes["AA"], nodes["AI"], link_capacity),
        Link(nodes["AO"], nodes["AI"], link_capacity),
        Link(nodes["AL"], nodes["AI"], link_capacity),
        Link(nodes["AP"], nodes["AI"], link_capacity),

        Link(nodes["AX"], nodes["B"], link_capacity),
        Link(nodes["AP"], nodes["AO"], link_capacity),
        Link(nodes["C"], nodes["AL"], link_capacity),
        Link(nodes["AX"], nodes["AL"], link_capacity),
        Link(nodes["AP"], nodes["AL"], link_capacity),
    ]

    for link in links:
        graph.add_link(link)

    return graph
