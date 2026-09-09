from domain.network_graph import NetworkGraph
from domain.link import Link
from domain.node import Node

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

NODE_LOCATIONS = {
    "A": "UFC Campus do Pici / PoP-CE",
    "B": "UECE Campus do Itaperi",
    "C": "UFC Campus Porangabuçu",
    "D": "FUNCAP",
    "E": "UFC Reitoria",
    "F": "UECE Centro de Humanidades",
    "G": "Instituto Atlântico",
    "H": "UFC Labomar",
    "I": "Escola de Saúde Pública do Ceará",
    "J": "Hospital Geral de Fortaleza",
    "K": "UNIFOR",
    "L": "SECITECE"
}


def create_test_graph_fortal() -> NetworkGraph:
    graph = NetworkGraph()

    nodes = {
        name: Node(name)
        for name in NODE_LOCATIONS.keys()
    }

    for node in nodes.values():
        graph.add_node(node)

    # ---------------------------------------------------------
    # Enlaces
    #
    # IMPORTANTE:
    # Os locais utilizados como nós são pontos reais.
    # As conexões e capacidades abaixo fazem parte da
    # topologia experimental do simulador.
    # ---------------------------------------------------------

    links = [

        # =====================================================
        # Rota 1
        #
        # UFC Pici
        #   ↓
        # UECE Itaperi
        #   ↓
        # SECITECE
        # =====================================================

        Link(
            nodes["A"],
            nodes["B"],
            40
        ),

        Link(
            nodes["B"],
            nodes["L"],
            40
        ),

        # =====================================================
        # Rota 2
        #
        # UFC Pici
        #   ↓
        # UFC Porangabuçu
        #   ↓
        # FUNCAP
        #   ↓
        # SECITECE
        # =====================================================

        Link(
            nodes["A"],
            nodes["C"],
            80
        ),

        Link(
            nodes["C"],
            nodes["D"],
            80
        ),

        Link(
            nodes["D"],
            nodes["L"],
            80
        ),

        # =====================================================
        # Rota 3
        #
        # UFC Pici
        #   ↓
        # UFC Reitoria
        #   ↓
        # UECE Centro de Humanidades
        #   ↓
        # Instituto Atlântico
        #   ↓
        # SECITECE
        # =====================================================

        Link(
            nodes["A"],
            nodes["E"],
            160
        ),

        Link(
            nodes["E"],
            nodes["F"],
            160
        ),

        Link(
            nodes["F"],
            nodes["G"],
            160
        ),

        Link(
            nodes["G"],
            nodes["L"],
            160
        ),

        # =====================================================
        # Rota 4
        #
        # UFC Pici
        #   ↓
        # UFC Labomar
        #   ↓
        # Escola de Saúde Pública
        #   ↓
        # Hospital Geral de Fortaleza
        #   ↓
        # UNIFOR
        #   ↓
        # SECITECE
        # =====================================================

        Link(
            nodes["A"],
            nodes["H"],
            320
        ),

        Link(
            nodes["H"],
            nodes["I"],
            320
        ),

        Link(
            nodes["I"],
            nodes["J"],
            320
        ),

        Link(
            nodes["J"],
            nodes["K"],
            320
        ),

        Link(
            nodes["K"],
            nodes["L"],
            320
        ),

        # =====================================================
        # Enlaces transversais
        # =====================================================

        # UECE Itaperi <-> UFC Porangabuçu
        Link(
            nodes["B"],
            nodes["C"],
            60
        ),

        # UECE Itaperi <-> UFC Reitoria
        Link(
            nodes["B"],
            nodes["E"],
            90
        ),

        # UFC Porangabuçu <-> UFC Reitoria
        Link(
            nodes["C"],
            nodes["E"],
            100
        ),

        # UFC Porangabuçu <-> UFC Labomar
        Link(
            nodes["C"],
            nodes["H"],
            120
        ),

        # FUNCAP <-> UECE Centro de Humanidades
        Link(
            nodes["D"],
            nodes["F"],
            110
        ),

        # FUNCAP <-> Instituto Atlântico
        Link(
            nodes["D"],
            nodes["G"],
            90
        ),

        # UFC Reitoria <-> UFC Labomar
        Link(
            nodes["E"],
            nodes["H"],
            180
        ),

        # UECE Centro de Humanidades
        # <-> Escola de Saúde Pública
        Link(
            nodes["F"],
            nodes["I"],
            200
        ),

        # Instituto Atlântico
        # <-> Hospital Geral de Fortaleza
        Link(
            nodes["G"],
            nodes["J"],
            220
        )
    ]

    # ---------------------------------------------------------
    # Adiciona os enlaces ao grafo
    # ---------------------------------------------------------

    for link in links:
        graph.add_link(link)

    return graph