"""Small graphs and independent assertions shared by allocator tests."""

import math

from domain.link import Link
from domain.network_graph import NetworkGraph
from domain.node import Node
from domain.slice_demand import SliceDemand
from domain.slice_request import SliceRequest
from domain.slice_result import SliceResult


def make_graph(edges, isolated=()):
    graph = NetworkGraph()
    for name in isolated:
        graph.add_node(Node(name))
    for source, target, capacity in edges:
        graph.add_link(Link(Node(source), Node(target), capacity))
    return graph


def make_request(
    source="A", destination="D", bandwidth=40, period="t1",
    request_id="request-1",
):
    demand = SliceDemand(id=period, bandwidth=bandwidth)
    request = SliceRequest(
        id=request_id,
        source=Node(source),
        destination=Node(destination),
        demands=[demand],
    )
    return request, demand


def assert_accepted(test_case, graph, request, demand, result):
    test_case.assertIsInstance(result, SliceResult)
    test_case.assertTrue(result.accepted)
    test_case.assertEqual(result.request_id, request.id)
    test_case.assertEqual(result.demand_id, demand.id)
    test_case.assertEqual(result.bandwidth, demand.bandwidth)
    test_case.assertTrue(result.path)
    test_case.assertEqual(result.path[0], request.source.name)
    test_case.assertEqual(result.path[-1], request.destination.name)
    test_case.assertEqual(len(result.path), len(set(result.path)))
    for link in graph.get_links_from_path(result.path):
        test_case.assertTrue(link.supports(demand.id, demand.bandwidth))


def assert_rejected(test_case, request, demand, result):
    test_case.assertIsInstance(result, SliceResult)
    test_case.assertFalse(result.accepted)
    test_case.assertEqual(result.request_id, request.id)
    test_case.assertEqual(result.demand_id, demand.id)
    test_case.assertEqual(result.path, [])


def graph_snapshot(graph):
    return (
        tuple(sorted(node.name for node in graph.nodes)),
        tuple(
            (link.source.name, link.target.name, link.capacity,
             tuple(link.allocations))
            for link in graph.links
        ),
    )


def all_feasible_paths(graph, source, destination, demand):
    """Enumerate only small graphs, without using an allocator as oracle."""
    paths = []

    def visit(path):
        if path[-1] == destination:
            paths.append(path)
            return
        for neighbor, link in graph.get_neighbors(Node(path[-1])):
            if neighbor.name not in path and link.supports(
                demand.id, demand.bandwidth
            ):
                visit(path + [neighbor.name])

    visit([source])
    return paths


def exponential_path_cost(graph, path, demand):
    return sum(
        math.exp(demand.bandwidth / link.available_bandwidth_at(demand.id))
        for link in graph.get_links_from_path(path)
    )
