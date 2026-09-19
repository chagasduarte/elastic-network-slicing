"""Behavioral checks for ant-colony routing with bounded, seeded searches."""

import random
import unittest

from algorithms.aco.aco_allocator import AcoAllocator
from contracts.slice_allocator import SliceAllocator
from domain.link_allocation import LinkAllocation
from domain.slice_result import SliceResult
from services.bandwidth_reservation_service import BandwidthReservationService
from tests.helpers import (
    all_feasible_paths,
    assert_accepted,
    assert_rejected,
    exponential_path_cost,
    graph_snapshot,
    make_graph,
    make_request,
)


class AcoAllocatorTests(unittest.TestCase):
    def allocator(self, **overrides):
        return AcoAllocator(
            **{"ants_count": 8, "iterations": 12, "seed": 42, **overrides}
        )

    def test_implements_shared_allocator_contract(self):
        self.assertIsInstance(self.allocator(), SliceAllocator)

    def test_exact_capacity_is_accepted_and_one_extra_unit_is_rejected(self):
        graph = make_graph([("A", "B", 100), ("B", "D", 40)])
        for bandwidth, accepted in ((40, True), (41, False)):
            with self.subTest(bandwidth=bandwidth):
                request, demand = make_request(bandwidth=bandwidth)
                result = self.allocator().allocate(graph, request, demand)
                if accepted:
                    assert_accepted(self, graph, request, demand, result)
                    self.assertEqual(result.path, ["A", "B", "D"])
                else:
                    assert_rejected(self, request, demand, result)

    def test_available_capacity_counts_competing_requests_in_current_period(self):
        graph = make_graph([("A", "D", 100)])
        graph.links[0].reserve(LinkAllocation("existing-1", "t1", 35))
        graph.links[0].reserve(LinkAllocation("existing-2", "t1", 25))
        graph.links[0].reserve(LinkAllocation("existing-3", "t2", 10))
        allocator = self.allocator()
        for bandwidth, period, accepted in (
            (40, "t1", True),
            (41, "t1", False),
            (90, "t2", True),
            (91, "t2", False),
            (100, "t3", True),
        ):
            with self.subTest(bandwidth=bandwidth, period=period):
                request, demand = make_request(bandwidth=bandwidth, period=period)
                result = allocator.allocate(graph, request, demand)
                if accepted:
                    assert_accepted(self, graph, request, demand, result)
                else:
                    assert_rejected(self, request, demand, result)

    def test_disconnected_destinations_are_rejected(self):
        graphs = (
            make_graph([], isolated=["A", "D"]),
            make_graph(
                [("A", "B", 100), ("B", "C", 100), ("C", "A", 100)],
                isolated=["D"],
            ),
        )
        request, demand = make_request()
        for index, graph in enumerate(graphs):
            with self.subTest(graph=index):
                result = self.allocator().allocate(graph, request, demand)
                assert_rejected(self, request, demand, result)

    @unittest.expectedFailure
    def test_source_equal_to_destination_needs_no_links(self):
        """ACO divide por zero ao depositar feromônio em caminho sem enlaces."""
        graph = make_graph([], isolated=["A"])
        request, demand = make_request(destination="A", bandwidth=320)
        result = self.allocator().allocate(graph, request, demand)
        assert_accepted(self, graph, request, demand, result)
        self.assertEqual(result.path, ["A"])

    def test_routing_does_not_change_graph_or_reserve_bandwidth(self):
        for bandwidth in (40, 101):
            with self.subTest(bandwidth=bandwidth):
                graph = make_graph([("A", "B", 100), ("B", "D", 100)])
                graph.links[0].reserve(LinkAllocation("existing", "t1", 20))
                request, demand = make_request(bandwidth=bandwidth)
                before = graph_snapshot(graph)
                result = self.allocator().allocate(graph, request, demand)
                if bandwidth == 40:
                    assert_accepted(self, graph, request, demand, result)
                else:
                    assert_rejected(self, request, demand, result)
                self.assertEqual(graph_snapshot(graph), before)

    def test_links_can_be_traversed_in_either_direction(self):
        graph = make_graph([("B", "A", 100), ("D", "B", 100)])
        for source, destination, path in (
            ("A", "D", ["A", "B", "D"]),
            ("D", "A", ["D", "B", "A"]),
        ):
            with self.subTest(source=source):
                request, demand = make_request(source=source, destination=destination)
                result = self.allocator().allocate(graph, request, demand)
                assert_accepted(self, graph, request, demand, result)
                self.assertEqual(result.path, path)

    def test_cycles_self_loops_and_dead_ends_produce_a_simple_route(self):
        graph = make_graph([
            ("A", "A", 100),
            ("A", "B", 100),
            ("B", "C", 100),
            ("C", "A", 100),
            ("B", "X", 100),
            ("C", "D", 100),
        ])
        request, demand = make_request()
        result = self.allocator().allocate(graph, request, demand)
        assert_accepted(self, graph, request, demand, result)
        self.assertNotIn("X", result.path)
        self.assertEqual(result.path, ["A", "C", "D"])

    def test_finds_minimum_additive_cost_on_seeded_small_graph(self):
        graph = make_graph([
            ("A", "D", 40),
            ("A", "B", 500),
            ("B", "D", 500),
            ("A", "C", 80),
            ("C", "D", 80),
            ("B", "C", 100),
        ])
        request, demand = make_request()
        feasible_paths = all_feasible_paths(graph, "A", "D", demand)
        expected_cost = min(
            exponential_path_cost(graph, path, demand) for path in feasible_paths
        )
        result = self.allocator().allocate(graph, request, demand)
        assert_accepted(self, graph, request, demand, result)
        self.assertEqual(result.path, ["A", "B", "D"])
        self.assertAlmostEqual(
            exponential_path_cost(graph, result.path, demand), expected_cost
        )

    def test_heuristic_weight_changes_route_with_one_ant(self):
        graph = make_graph([
            ("A", "B", 40), ("B", "D", 40),
            ("A", "C", 400), ("C", "D", 400),
        ])
        request, demand = make_request()
        # A single sampled route exposes the heuristic's effect before learning.
        uniform = self.allocator(ants_count=1, iterations=1, beta=0, seed=1).allocate(
            graph, request, demand
        )
        weighted = self.allocator(ants_count=1, iterations=1, beta=2, seed=1).allocate(
            graph, request, demand
        )
        assert_accepted(self, graph, request, demand, uniform)
        assert_accepted(self, graph, request, demand, weighted)
        self.assertEqual(uniform.path, ["A", "B", "D"])
        self.assertEqual(weighted.path, ["A", "C", "D"])

    def test_additional_ants_can_improve_a_limited_search(self):
        graph = make_graph([
            ("A", "B", 40), ("B", "D", 40),
            ("A", "C", 400), ("C", "D", 400),
        ])
        request, demand = make_request()
        single = self.allocator(ants_count=1, iterations=1, beta=0, seed=1).allocate(
            graph, request, demand
        )
        multiple = self.allocator(ants_count=8, iterations=1, beta=0, seed=1).allocate(
            graph, request, demand
        )
        assert_accepted(self, graph, request, demand, single)
        assert_accepted(self, graph, request, demand, multiple)
        self.assertLess(
            exponential_path_cost(graph, multiple.path, demand),
            exponential_path_cost(graph, single.path, demand),
        )

    def test_previous_result_does_not_bias_route_selection(self):
        graph = make_graph([
            ("A", "B", 100), ("B", "D", 100),
            ("A", "C", 98), ("C", "D", 98),
        ])
        request, demand = make_request()
        baseline = self.allocator().allocate(graph, request, demand)
        assert_accepted(self, graph, request, demand, baseline)
        self.assertEqual(baseline.path, ["A", "B", "D"])
        previous_results = (
            SliceResult(request.id, "t0", True, ["A", "C", "D"], 30),
            SliceResult("unrelated", "t0", True, ["A", "C", "D"], 30),
            SliceResult(request.id, "t0", False, [], 0),
        )
        for previous in previous_results:
            with self.subTest(previous=previous):
                result = self.allocator().allocate(graph, request, demand, previous)
                self.assertEqual(result, baseline)

    def test_new_reservations_and_demands_change_later_routes(self):
        graph = make_graph([
            ("A", "B", 100), ("B", "D", 100),
            ("A", "C", 80), ("C", "D", 80),
        ])
        allocator = self.allocator()
        request, demand = make_request()
        first = allocator.allocate(graph, request, demand)
        assert_accepted(self, graph, request, demand, first)
        self.assertEqual(first.path, ["A", "B", "D"])
        BandwidthReservationService().reserve(
            graph.get_links_from_path(first.path),
            LinkAllocation("another-request", demand.id, 80),
        )
        second = allocator.allocate(graph, request, demand, first)
        assert_accepted(self, graph, request, demand, second)
        self.assertEqual(second.path, ["A", "C", "D"])

        request, larger_demand = make_request(bandwidth=81)
        rejected = allocator.allocate(graph, request, larger_demand, second)
        assert_rejected(self, request, larger_demand, rejected)

        request, next_period = make_request(bandwidth=81, period="t2")
        final = allocator.allocate(graph, request, next_period, rejected)
        assert_accepted(self, graph, request, next_period, final)
        self.assertEqual(final.path, ["A", "B", "D"])

    def test_destination_changes_between_calls(self):
        graph = make_graph([("A", "B", 100), ("B", "D", 100)])
        allocator = self.allocator()
        request, demand = make_request()
        previous = allocator.allocate(graph, request, demand)
        assert_accepted(self, graph, request, demand, previous)
        request, demand = make_request(destination="B")
        result = allocator.allocate(graph, request, demand, previous)
        assert_accepted(self, graph, request, demand, result)
        self.assertEqual(result.path, ["A", "B"])

    def test_same_allocator_can_route_a_new_graph(self):
        allocator = self.allocator()
        graph = make_graph([("A", "D", 100)])
        request, demand = make_request()
        first = allocator.allocate(graph, request, demand)
        assert_accepted(self, graph, request, demand, first)
        graph = make_graph([("X", "Y", 100), ("Y", "Z", 100)])
        request, demand = make_request(source="X", destination="Z")
        result = allocator.allocate(graph, request, demand, first)
        assert_accepted(self, graph, request, demand, result)
        self.assertEqual(result.path, ["X", "Y", "Z"])

    def test_same_seed_reproduces_a_sequence_of_allocations(self):
        graph = make_graph([
            ("A", "B", 100), ("B", "D", 100),
            ("A", "C", 100), ("C", "D", 100),
        ])
        request, demand = make_request()
        for seed in (0, 1, 42):
            with self.subTest(seed=seed):
                first = self.allocator(seed=seed)
                second = self.allocator(seed=seed)
                for _ in range(3):
                    left = first.allocate(graph, request, demand)
                    right = second.allocate(graph, request, demand)
                    assert_accepted(self, graph, request, demand, left)
                    self.assertEqual(left, right)

    def test_search_does_not_change_global_random_state(self):
        graph = make_graph([
            ("A", "B", 100), ("B", "D", 100),
            ("A", "C", 100), ("C", "D", 100),
        ])
        request, demand = make_request()
        original_state = random.getstate()
        try:
            result = self.allocator().allocate(graph, request, demand)
            assert_accepted(self, graph, request, demand, result)
            self.assertEqual(random.getstate(), original_state)
        finally:
            random.setstate(original_state)


if __name__ == "__main__":
    unittest.main()
