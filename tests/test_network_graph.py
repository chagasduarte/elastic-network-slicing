import random
import unittest

from domain.link import Link
from domain.network_graph import NetworkGraph
from domain.node import Node


def linear_neighbors(links, node):
    out = []
    for link in links:
        if link.source == node:
            out.append((link.target, link))
        elif link.target == node:
            out.append((link.source, link))
    return out


def linear_link(links, a, b):
    for link in links:
        if (link.source.name, link.target.name) in ((a, b), (b, a)):
            return link
    return None


class NetworkGraphTest(unittest.TestCase):
    def test_adjacencia_equivale_a_varredura_linear(self):
        rng = random.Random(1)
        nodes = [Node(str(i)) for i in range(15)]
        graph = NetworkGraph()
        for _ in range(60):  # inclui enlaces paralelos e em sentidos opostos
            a, b = rng.sample(nodes, 2)
            graph.add_link(Link(a, b, 100))
        for node in nodes:
            self.assertEqual(graph.get_neighbors(node), linear_neighbors(graph.links, node))
        for a in nodes:
            for b in nodes:
                self.assertIs(graph.get_link(a.name, b.name),
                              linear_link(graph.links, a.name, b.name))

    def test_get_node_e_no_desconhecido(self):
        graph = NetworkGraph()
        graph.add_link(Link(Node("A"), Node("B"), 10))
        self.assertEqual(graph.get_node("A"), Node("A"))
        self.assertIsNone(graph.get_node("Z"))
        self.assertEqual(graph.get_neighbors(Node("Z")), [])


if __name__ == "__main__":
    unittest.main()
