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
    "Aachen": "Aachen, Alemanha",
    "Augsburg": "Augsburg, Alemanha",
    "Bayreuth": "Bayreuth, Alemanha",
    "Berlin": "Berlim, Alemanha",
    "Bielefeld": "Bielefeld, Alemanha",
    "Braunschweig": "Braunschweig, Alemanha",
    "Bremen": "Bremen, Alemanha",
    "Bremerhaven": "Bremerhaven, Alemanha",
    "Chemnitz": "Chemnitz, Alemanha",
    "Darmstadt": "Darmstadt, Alemanha",
    "Dortmund": "Dortmund, Alemanha",
    "Dresden": "Dresden, Alemanha",
    "Duesseldorf": "Düsseldorf, Alemanha",
    "Erfurt": "Erfurt, Alemanha",
    "Essen": "Essen, Alemanha",
    "Flensburg": "Flensburg, Alemanha",
    "Frankfurt": "Frankfurt, Alemanha",
    "Freiburg": "Freiburg, Alemanha",
    "Fulda": "Fulda, Alemanha",
    "Giessen": "Giessen, Alemanha",
    "Greifswald": "Greifswald, Alemanha",
    "Hamburg": "Hamburgo, Alemanha",
    "Hannover": "Hannover, Alemanha",
    "Kaiserslautern": "Kaiserslautern, Alemanha",
    "Karlsruhe": "Karlsruhe, Alemanha",
    "Kassel": "Kassel, Alemanha",
    "Kempten": "Kempten, Alemanha",
    "Kiel": "Kiel, Alemanha",
    "Koblenz": "Koblenz, Alemanha",
    "Koeln": "Colônia, Alemanha",
    "Konstanz": "Konstanz, Alemanha",
    "Leipzig": "Leipzig, Alemanha",
    "Magdeburg": "Magdeburg, Alemanha",
    "Mannheim": "Mannheim, Alemanha",
    "Muenchen": "Munique, Alemanha",
    "Muenster": "Münster, Alemanha",
    "Norden": "Norden, Alemanha",
    "Nuernberg": "Nuremberg, Alemanha",
    "Oldenburg": "Oldenburg, Alemanha",
    "Osnabrueck": "Osnabrück, Alemanha",
    "Passau": "Passau, Alemanha",
    "Regensburg": "Regensburg, Alemanha",
    "Saarbruecken": "Saarbrücken, Alemanha",
    "Schwerin": "Schwerin, Alemanha",
    "Siegen": "Siegen, Alemanha",
    "Stuttgart": "Stuttgart, Alemanha",
    "Trier": "Trier, Alemanha",
    "Ulm": "Ulm, Alemanha",
    "Wesel": "Wesel, Alemanha",
    "Wuerzburg": "Würzburg, Alemanha",
}

NODE_COORDINATES = {
    "Aachen": (6.04, 50.76),
    "Augsburg": (10.90, 48.33),
    "Bayreuth": (11.59, 49.93),
    "Berlin": (13.39, 52.52),
    "Bielefeld": (8.50, 52.04),
    "Braunschweig": (10.55, 52.28),
    "Bremen": (8.85, 53.11),
    "Bremerhaven": (8.58, 53.54),
    "Chemnitz": (12.93, 50.84),
    "Darmstadt": (8.65, 49.89),
    "Dortmund": (7.45, 51.51),
    "Dresden": (13.73, 51.03),
    "Duesseldorf": (6.77, 51.25),
    "Erfurt": (11.04, 50.98),
    "Essen": (7.02, 51.46),
    "Flensburg": (9.45, 54.77),
    "Frankfurt": (8.71, 50.12),
    "Freiburg": (7.80, 47.98),
    "Fulda": (9.69, 50.56),
    "Giessen": (8.67, 50.57),
    "Greifswald": (13.40, 54.09),
    "Hamburg": (9.99, 53.57),
    "Hannover": (9.72, 52.38),
    "Kaiserslautern": (7.75, 49.43),
    "Karlsruhe": (8.41, 49.01),
    "Kassel": (9.51, 51.32),
    "Kempten": (10.32, 47.72),
    "Kiel": (10.12, 54.34),
    "Koblenz": (7.52, 50.40),
    "Koeln": (6.87, 50.94),
    "Konstanz": (9.18, 47.66),
    "Leipzig": (12.38, 51.34),
    "Magdeburg": (11.64, 52.14),
    "Mannheim": (8.49, 49.49),
    "Muenchen": (11.57, 48.15),
    "Muenster": (7.60, 51.97),
    "Norden": (7.21, 53.60),
    "Nuernberg": (11.03, 49.57),
    "Oldenburg": (8.21, 53.11),
    "Osnabrueck": (8.03, 52.28),
    "Passau": (13.46, 48.57),
    "Regensburg": (12.09, 49.00),
    "Saarbruecken": (7.03, 49.23),
    "Schwerin": (11.45, 53.55),
    "Siegen": (8.03, 50.91),
    "Stuttgart": (9.10, 48.74),
    "Trier": (6.68, 49.75),
    "Ulm": (9.99, 48.40),
    "Wesel": (6.37, 51.39),
    "Wuerzburg": (9.97, 49.78),
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
        Link(nodes["Duesseldorf"], nodes["Essen"], link_capacity),
        Link(nodes["Dortmund"], nodes["Essen"], link_capacity),
        Link(nodes["Wesel"], nodes["Essen"], link_capacity),
        Link(nodes["Koeln"], nodes["Duesseldorf"], link_capacity),
        Link(nodes["Aachen"], nodes["Koeln"], link_capacity),
        Link(nodes["Koblenz"], nodes["Koeln"], link_capacity),
        Link(nodes["Muenster"], nodes["Dortmund"], link_capacity),
        Link(nodes["Siegen"], nodes["Dortmund"], link_capacity),
        Link(nodes["Kassel"], nodes["Dortmund"], link_capacity),
        Link(nodes["Wesel"], nodes["Aachen"], link_capacity),
        Link(nodes["Trier"], nodes["Aachen"], link_capacity),
        Link(nodes["Bielefeld"], nodes["Muenster"], link_capacity),
        Link(nodes["Osnabrueck"], nodes["Muenster"], link_capacity),
        Link(nodes["Siegen"], nodes["Koblenz"], link_capacity),
        Link(nodes["Frankfurt"], nodes["Koblenz"], link_capacity),
        Link(nodes["Kaiserslautern"], nodes["Koblenz"], link_capacity),
        Link(nodes["Trier"], nodes["Koblenz"], link_capacity),
        Link(nodes["Bielefeld"], nodes["Siegen"], link_capacity),
        Link(nodes["Giessen"], nodes["Siegen"], link_capacity),
        Link(nodes["Oldenburg"], nodes["Wesel"], link_capacity),
        Link(nodes["Norden"], nodes["Wesel"], link_capacity),

        Link(nodes["Leipzig"], nodes["Berlin"], link_capacity),
        Link(nodes["Dresden"], nodes["Berlin"], link_capacity),
        Link(nodes["Schwerin"], nodes["Berlin"], link_capacity),
        Link(nodes["Magdeburg"], nodes["Berlin"], link_capacity),
        Link(nodes["Greifswald"], nodes["Berlin"], link_capacity),

        Link(nodes["Dresden"], nodes["Leipzig"], link_capacity),
        Link(nodes["Erfurt"], nodes["Leipzig"], link_capacity),
        Link(nodes["Magdeburg"], nodes["Leipzig"], link_capacity),
        Link(nodes["Bayreuth"], nodes["Leipzig"], link_capacity),

        Link(nodes["Erfurt"], nodes["Dresden"], link_capacity),
        Link(nodes["Chemnitz"], nodes["Dresden"], link_capacity),
        Link(nodes["Chemnitz"], nodes["Erfurt"], link_capacity),
        Link(nodes["Kassel"], nodes["Erfurt"], link_capacity),
        Link(nodes["Wuerzburg"], nodes["Erfurt"], link_capacity),
        Link(nodes["Bayreuth"], nodes["Chemnitz"], link_capacity),

        Link(nodes["Magdeburg"], nodes["Schwerin"], link_capacity),
        Link(nodes["Greifswald"], nodes["Schwerin"], link_capacity),
        Link(nodes["Hamburg"], nodes["Schwerin"], link_capacity),
        Link(nodes["Kiel"], nodes["Schwerin"], link_capacity),

        Link(nodes["Braunschweig"], nodes["Magdeburg"], link_capacity),

        Link(nodes["Kiel"], nodes["Hamburg"], link_capacity),
        Link(nodes["Hannover"], nodes["Hamburg"], link_capacity),
        Link(nodes["Braunschweig"], nodes["Hamburg"], link_capacity),

        Link(nodes["Oldenburg"], nodes["Bremen"], link_capacity),
        Link(nodes["Bremerhaven"], nodes["Bremen"], link_capacity),
        Link(nodes["Hannover"], nodes["Bremen"], link_capacity),

        Link(nodes["Flensburg"], nodes["Kiel"], link_capacity),
        Link(nodes["Norden"], nodes["Oldenburg"], link_capacity),
        Link(nodes["Osnabrueck"], nodes["Oldenburg"], link_capacity),
        Link(nodes["Bremerhaven"], nodes["Flensburg"], link_capacity),

        Link(nodes["Bielefeld"], nodes["Hannover"], link_capacity),
        Link(nodes["Braunschweig"], nodes["Hannover"], link_capacity),
        Link(nodes["Osnabrueck"], nodes["Hannover"], link_capacity),
        Link(nodes["Braunschweig"], nodes["Bielefeld"], link_capacity),
        Link(nodes["Kassel"], nodes["Braunschweig"], link_capacity),

        Link(nodes["Giessen"], nodes["Kassel"], link_capacity),
        Link(nodes["Fulda"], nodes["Kassel"], link_capacity),

        Link(nodes["Darmstadt"], nodes["Frankfurt"], link_capacity),
        Link(nodes["Giessen"], nodes["Frankfurt"], link_capacity),
        Link(nodes["Fulda"], nodes["Frankfurt"], link_capacity),

        Link(nodes["Mannheim"], nodes["Darmstadt"], link_capacity),
        Link(nodes["Kaiserslautern"], nodes["Darmstadt"], link_capacity),

        Link(nodes["Karlsruhe"], nodes["Mannheim"], link_capacity),
        Link(nodes["Saarbruecken"], nodes["Kaiserslautern"], link_capacity),
        Link(nodes["Karlsruhe"], nodes["Kaiserslautern"], link_capacity),
        Link(nodes["Fulda"], nodes["Giessen"], link_capacity),
        Link(nodes["Saarbruecken"], nodes["Trier"], link_capacity),
        Link(nodes["Wuerzburg"], nodes["Fulda"], link_capacity),

        Link(nodes["Karlsruhe"], nodes["Saarbruecken"], link_capacity),
        Link(nodes["Karlsruhe"], nodes["Stuttgart"], link_capacity),
        Link(nodes["Ulm"], nodes["Stuttgart"], link_capacity),
        Link(nodes["Konstanz"], nodes["Stuttgart"], link_capacity),
        Link(nodes["Wuerzburg"], nodes["Stuttgart"], link_capacity),
        Link(nodes["Freiburg"], nodes["Karlsruhe"], link_capacity),

        Link(nodes["Augsburg"], nodes["Ulm"], link_capacity),
        Link(nodes["Freiburg"], nodes["Konstanz"], link_capacity),
        Link(nodes["Kempten"], nodes["Konstanz"], link_capacity),

        Link(nodes["Augsburg"], nodes["Muenchen"], link_capacity),
        Link(nodes["Kempten"], nodes["Muenchen"], link_capacity),
        Link(nodes["Passau"], nodes["Muenchen"], link_capacity),
        Link(nodes["Nuernberg"], nodes["Muenchen"], link_capacity),
        Link(nodes["Regensburg"], nodes["Muenchen"], link_capacity),

        Link(nodes["Wuerzburg"], nodes["Augsburg"], link_capacity),
        Link(nodes["Regensburg"], nodes["Passau"], link_capacity),
        Link(nodes["Bayreuth"], nodes["Nuernberg"], link_capacity),
        Link(nodes["Wuerzburg"], nodes["Nuernberg"], link_capacity),
        Link(nodes["Regensburg"], nodes["Nuernberg"], link_capacity),
    ]

    for link in links:
        graph.add_link(link)

    return graph
