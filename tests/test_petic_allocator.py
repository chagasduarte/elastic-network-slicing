"""Behavioral checks for PETIC routing and its bandwidth-dependent weights."""

import math
import unittest

from algorithms.petic.petic_allocator import PeticAllocator
from algorithms.petic.petic_weight_calculator import PeticWeightCalculator
from contracts.slice_allocator import SliceAllocator
from domain.link_allocation import LinkAllocation
from domain.slice_demand import SliceDemand
from domain.slice_result import SliceResult
from pathfinding.dijkstra_path_finder import DijkstraPathFinder
from tests.helpers import (
    all_feasible_paths,
    assert_accepted,
    assert_rejected,
    exponential_path_cost,
    graph_snapshot,
    make_graph,
    make_request,
)


class PeticWeightCalculatorTests(unittest.TestCase):
    def test_weight_uses_requested_bandwidth_and_available_capacity(self):
        calculator = PeticWeightCalculator()
        for capacity, reserved, bandwidth in ((100, 0, 40), (100, 20, 40),
                                               (100, 60, 40), (500, 0, 15)):
            with self.subTest(capacity=capacity, reserved=reserved,
                              bandwidth=bandwidth):
                link = make_graph([("A", "D", capacity)]).links[0]
                if reserved:
                    link.reserve(LinkAllocation("other-request", "t1", reserved))
                demand = SliceDemand("t1", bandwidth)
                self.assertAlmostEqual(
                    calculator.calculate(link, demand),
                    math.exp(bandwidth / (capacity - reserved)),
                )

    def test_weight_counts_all_reservations_only_in_requested_period(self):
        link = make_graph([("A", "D", 100)]).links[0]
        link.reserve(LinkAllocation("request-1", "t1", 20))
        link.reserve(LinkAllocation("request-2", "t1", 30))
        link.reserve(LinkAllocation("request-3", "t2", 10))
        calculator = PeticWeightCalculator()
        self.assertAlmostEqual(calculator.calculate(link, SliceDemand("t1", 40)),
                               math.exp(40 / 50))
        self.assertAlmostEqual(calculator.calculate(link, SliceDemand("t2", 40)),
                               math.exp(40 / 90))
        self.assertAlmostEqual(calculator.calculate(link, SliceDemand("t3", 40)),
                               math.exp(40 / 100))

    def test_insufficient_or_fully_reserved_capacity_has_infinite_weight(self):
        calculator = PeticWeightCalculator()
        for reserved in (61, 100):
            with self.subTest(reserved=reserved):
                link = make_graph([("A", "D", 100)]).links[0]
                link.reserve(LinkAllocation("other-request", "t1", reserved))
                self.assertEqual(calculator.calculate(link, SliceDemand("t1", 40)),
                                 math.inf)


class PeticAllocatorTests(unittest.TestCase):
    def allocator(self):
        return PeticAllocator(DijkstraPathFinder(), PeticWeightCalculator())

    def test_implements_shared_allocator_contract(self):
        self.assertIsInstance(self.allocator(), SliceAllocator)

    def test_selects_minimum_additive_cost_among_all_feasible_paths(self):
        graph = make_graph([
            ("A", "D", 40),
            ("A", "B", 500), ("B", "D", 500),
            ("A", "C", 80), ("C", "D", 80), ("B", "C", 100),
        ])
        request, demand = make_request()
        feasible_paths = all_feasible_paths(graph, "A", "D", demand)
        expected_cost = min(exponential_path_cost(graph, path, demand)
                            for path in feasible_paths)
        result = self.allocator().allocate(graph, request, demand)
        assert_accepted(self, graph, request, demand, result)
        self.assertAlmostEqual(exponential_path_cost(graph, result.path, demand),
                               expected_cost)
        self.assertEqual(result.path, ["A", "B", "D"])

    def test_exact_capacity_is_accepted_and_insufficient_capacity_is_rejected(self):
        graph = make_graph([("A", "B", 100), ("B", "D", 40)])
        for bandwidth, accepted in ((40, True), (41, False)):
            with self.subTest(bandwidth=bandwidth):
                request, demand = make_request(bandwidth=bandwidth)
                result = self.allocator().allocate(graph, request, demand)
                if accepted:
                    assert_accepted(self, graph, request, demand, result)
                else:
                    assert_rejected(self, request, demand, result)
                    self.assertEqual(result.bandwidth, 0)

    def test_capacity_counts_competing_requests_in_the_same_period(self):
        graph = make_graph([("A", "D", 100)])
        graph.links[0].reserve(LinkAllocation("other-1", "t1", 20))
        graph.links[0].reserve(LinkAllocation("other-2", "t1", 40))
        allocator = self.allocator()
        for bandwidth, period, accepted in ((40, "t1", True), (41, "t1", False),
                                             (100, "t2", True)):
            with self.subTest(bandwidth=bandwidth, period=period):
                request, demand = make_request(bandwidth=bandwidth, period=period)
                result = allocator.allocate(graph, request, demand)
                if accepted:
                    assert_accepted(self, graph, request, demand, result)
                else:
                    assert_rejected(self, request, demand, result)

    def test_routing_does_not_modify_graph_or_reserve_bandwidth(self):
        graph = make_graph([("A", "B", 100), ("B", "D", 100)])
        graph.links[0].reserve(LinkAllocation("other-request", "t1", 20))
        before = graph_snapshot(graph)
        allocator = self.allocator()
        for bandwidth, accepted in ((40, True), (81, False)):
            with self.subTest(bandwidth=bandwidth):
                request, demand = make_request(bandwidth=bandwidth)
                result = allocator.allocate(graph, request, demand)
                if accepted:
                    assert_accepted(self, graph, request, demand, result)
                else:
                    assert_rejected(self, request, demand, result)
                self.assertEqual(graph_snapshot(graph), before)

    def test_previous_route_is_preferred_when_bandwidth_decreases_or_stays_equal(self):
        graph = make_graph([
            ("A", "B", 500), ("B", "D", 500),
            ("A", "C", 100), ("C", "D", 100),
        ])
        request, demand = make_request()
        self.assertEqual(self.allocator().allocate(graph, request, demand).path,
                         ["A", "B", "D"])
        for previous_bandwidth in (40, 60):
            with self.subTest(previous_bandwidth=previous_bandwidth):
                previous = SliceResult(request.id, "t0", True,
                                       ["A", "C", "D"], previous_bandwidth)
                result = self.allocator().allocate(graph, request, demand, previous)
                assert_accepted(self, graph, request, demand, result)
                self.assertEqual(result.path, previous.path)

    def test_increased_bandwidth_removes_previous_route_preference(self):
        graph = make_graph([
            ("A", "B", 500), ("B", "D", 500),
            ("A", "C", 100), ("C", "D", 100),
        ])
        request, demand = make_request()
        previous = SliceResult(request.id, "t0", True, ["A", "C", "D"], 30)
        result = self.allocator().allocate(graph, request, demand, previous)
        assert_accepted(self, graph, request, demand, result)
        self.assertEqual(result.path, ["A", "B", "D"])

    def test_rejected_previous_result_does_not_enable_route_preference(self):
        graph = make_graph([
            ("A", "B", 500), ("B", "D", 500),
            ("A", "C", 100), ("C", "D", 100),
        ])
        request, demand = make_request()
        for path, bandwidth in (([], 0), (["A", "C", "D"], 60)):
            with self.subTest(path=path, bandwidth=bandwidth):
                previous = SliceResult(request.id, "t0", False, path, bandwidth)
                result = self.allocator().allocate(graph, request, demand, previous)
                assert_accepted(self, graph, request, demand, result)
                self.assertEqual(result.path, ["A", "B", "D"])

    def test_blocked_previous_route_uses_feasible_alternative(self):
        graph = make_graph([
            ("A", "B", 100), ("B", "D", 100),
            ("A", "C", 100), ("C", "D", 100),
        ])
        graph.get_link("C", "D").reserve(LinkAllocation("other-request", "t1", 61))
        request, demand = make_request()
        previous = SliceResult(request.id, "t0", True, ["A", "C", "D"], 60)
        result = self.allocator().allocate(graph, request, demand, previous)
        assert_accepted(self, graph, request, demand, result)
        self.assertEqual(result.path, ["A", "B", "D"])

    def test_new_reservations_change_the_next_decision(self):
        graph = make_graph([
            ("A", "B", 100), ("B", "D", 100),
            ("A", "C", 80), ("C", "D", 80),
        ])
        request, demand = make_request()
        allocator = self.allocator()
        first = allocator.allocate(graph, request, demand)
        self.assertEqual(first.path, ["A", "B", "D"])
        for link in graph.get_links_from_path(first.path):
            link.reserve(LinkAllocation("other-request", "t1", 80))
        result = allocator.allocate(graph, request, demand, first)
        assert_accepted(self, graph, request, demand, result)
        self.assertEqual(result.path, ["A", "C", "D"])

    def test_cycles_dead_ends_and_reversed_links_produce_a_simple_route(self):
        graph = make_graph([
            ("B", "A", 100), ("C", "B", 100), ("A", "C", 100),
            ("X", "B", 100), ("D", "C", 100), ("A", "A", 100),
        ])
        request, demand = make_request()
        result = self.allocator().allocate(graph, request, demand)
        assert_accepted(self, graph, request, demand, result)
        self.assertEqual(result.path, ["A", "C", "D"])

    def test_disconnected_or_edgeless_graph_returns_rejection(self):
        request, demand = make_request()
        graphs = (
            make_graph([("A", "B", 100), ("B", "C", 100), ("C", "A", 100)],
                       isolated=["D"]),
            make_graph([], isolated=["A", "D"]),
        )
        for graph in graphs:
            with self.subTest(graph=graph):
                result = self.allocator().allocate(graph, request, demand)
                assert_rejected(self, request, demand, result)
                self.assertEqual(result.bandwidth, 0)

    def test_source_equal_to_destination_needs_no_links(self):
        graph = make_graph([], isolated=["A"])
        request, demand = make_request(destination="A", bandwidth=320)
        result = self.allocator().allocate(graph, request, demand)
        assert_accepted(self, graph, request, demand, result)
        self.assertEqual(result.path, ["A"])

    def test_missing_endpoints_raise_value_error(self):
        graph = make_graph([("A", "D", 100)])
        for source, destination in (("missing", "D"), ("A", "missing"),
                                    ("missing", "missing")):
            with self.subTest(source=source, destination=destination):
                request, demand = make_request(source=source, destination=destination)
                with self.assertRaises(ValueError):
                    self.allocator().allocate(graph, request, demand)


if __name__ == "__main__":
    unittest.main()
