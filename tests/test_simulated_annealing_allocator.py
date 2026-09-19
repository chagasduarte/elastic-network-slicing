"""Behavioral and regression tests for simulated annealing allocation."""

import random
import unittest
from unittest.mock import Mock

from algorithms.sa.simulated_annealing_allocator import SimulatedAnnealingAllocator
from algorithms.sa.simulated_annealing_config import SimulatedAnnealingConfig
from algorithms.sa.simulated_annealing_cost_calculator import (
    SimulatedAnnealingCostCalculator,
)
from algorithms.sa.simulated_annealing_neighbor_generator import (
    SimulatedAnnealingNeighborGenerator,
)
from domain.link_allocation import LinkAllocation
from domain.slice_result import SliceResult
from pathfinding.dijkstra_path_finder import DijkstraPathFinder
from services.bandwidth_reservation_service import BandwidthReservationService
from tests.helpers import (
    assert_accepted, assert_rejected, graph_snapshot, make_graph, make_request,
)


def make_allocator(config=None, seed=42, neighbors=None, random_generator=None):
    config = config if config is not None else SimulatedAnnealingConfig()
    generator = (
        random_generator if random_generator is not None else random.Random(seed)
    )
    return SimulatedAnnealingAllocator(
        path_finder=DijkstraPathFinder(),
        cost_calculator=SimulatedAnnealingCostCalculator(config),
        neighbor_generator=(
            neighbors if neighbors is not None
            else SimulatedAnnealingNeighborGenerator(config, generator)
        ),
        reservation_service=BandwidthReservationService(),
        config=config,
        random_generator=generator,
    )


class SimulatedAnnealingAllocatorTests(unittest.TestCase):
    def test_rejection_returns_demand_id_without_type_error(self):
        request, demand = make_request(period="period-with-no-route")
        graphs = (
            make_graph([], isolated=("A", "D")),
            make_graph([("A", "B", 100)], isolated=("D",)),
            make_graph([("A", "B", 100), ("B", "D", 39)]),
        )
        for graph in graphs:
            with self.subTest(graph=graph):
                before = graph_snapshot(graph)
                # Exercise allocate, including the previously broken
                # SliceResult(period_id=...) rejection constructor.
                result = make_allocator().allocate(graph, request, demand)
                assert_rejected(self, request, demand, result)
                self.assertEqual(graph_snapshot(graph), before)

    def test_capacity_accounts_for_other_requests_only_in_same_period(self):
        graph = make_graph([("A", "D", 100)])
        graph.links[0].reserve(LinkAllocation("other-request", "t1", 60))
        allocator = make_allocator()
        for bandwidth, period, accepted in (
            (40, "t1", True), (41, "t1", False), (100, "t2", True),
        ):
            with self.subTest(bandwidth=bandwidth, period=period):
                request, demand = make_request(bandwidth=bandwidth, period=period)
                before = graph_snapshot(graph)
                result = allocator.allocate(graph, request, demand)
                if accepted:
                    assert_accepted(self, graph, request, demand, result)
                else:
                    assert_rejected(self, request, demand, result)
                self.assertEqual(graph_snapshot(graph), before)

    def test_improves_initial_shortest_path_using_available_capacity(self):
        graph = make_graph([
            ("A", "D", 40), ("A", "B", 500), ("B", "D", 500),
        ])
        request, demand = make_request()
        result = make_allocator().allocate(graph, request, demand)
        assert_accepted(self, graph, request, demand, result)
        # Dijkstra starts with A-D (one hop). Its utilization is 100%;
        # A-B-D has two hops but only 8% utilization on each link.
        self.assertEqual(result.path, ["A", "B", "D"])

    def test_accepted_previous_path_changes_preference(self):
        graph = make_graph([
            ("A", "B", 100), ("B", "D", 100),
            ("A", "C", 100), ("C", "D", 100),
        ])
        request, demand = make_request()
        previous = SliceResult(request.id, "t0", True, ["A", "C", "D"], 30)
        result = make_allocator().allocate(graph, request, demand, previous)
        assert_accepted(self, graph, request, demand, result)
        self.assertEqual(result.path, previous.path)
        rejected = SliceResult(request.id, "t0", False, previous.path, 0)
        without_history = make_allocator().allocate(graph, request, demand)
        with_rejected_history = make_allocator().allocate(
            graph, request, demand, rejected
        )
        self.assertEqual(without_history, with_rejected_history)
        self.assertEqual(without_history.path, ["A", "B", "D"])

    def test_previous_path_cannot_override_current_capacity(self):
        graph = make_graph([
            ("A", "B", 100), ("B", "D", 100),
            ("A", "C", 30), ("C", "D", 30),
        ])
        request, demand = make_request()
        previous = SliceResult(request.id, "t0", True, ["A", "C", "D"], 30)
        result = make_allocator().allocate(graph, request, demand, previous)
        assert_accepted(self, graph, request, demand, result)
        self.assertEqual(result.path, ["A", "B", "D"])

    def test_new_reservations_change_route_without_internal_reservations(self):
        graph = make_graph([
            ("A", "B", 100), ("B", "D", 100),
            ("A", "C", 80), ("C", "D", 80),
        ])
        request, demand = make_request()
        allocator = make_allocator()
        first = allocator.allocate(graph, request, demand)
        self.assertEqual(first.path, ["A", "B", "D"])
        self.assertTrue(all(not link.allocations for link in graph.links))
        BandwidthReservationService().reserve(
            graph.get_links_from_path(first.path),
            LinkAllocation("other-request", demand.id, 80),
        )
        before = graph_snapshot(graph)
        second = allocator.allocate(graph, request, demand, first)
        assert_accepted(self, graph, request, demand, second)
        self.assertEqual(second.path, ["A", "C", "D"])
        self.assertEqual(graph_snapshot(graph), before)

    def test_cycles_and_dead_ends_return_a_simple_path(self):
        graph = make_graph([
            ("B", "A", 100), ("B", "C", 100), ("C", "A", 100),
            ("B", "X", 100), ("D", "C", 100),
        ])
        request, demand = make_request()
        result = make_allocator().allocate(graph, request, demand)
        assert_accepted(self, graph, request, demand, result)
        self.assertEqual(result.path, ["A", "C", "D"])

    def test_same_seed_reproduces_a_sequence_of_demands(self):
        graph = make_graph([
            ("A", "B", 100), ("B", "D", 100),
            ("A", "C", 150), ("C", "D", 150), ("B", "C", 100),
        ])
        first, second = make_allocator(), make_allocator()
        previous_first = previous_second = None
        for index, bandwidth in enumerate((40, 50, 15), start=1):
            request, demand = make_request(bandwidth=bandwidth, period=f"t{index}")
            previous_first = first.allocate(graph, request, demand, previous_first)
            previous_second = second.allocate(graph, request, demand, previous_second)
            self.assertEqual(previous_first, previous_second)

    def test_identical_endpoints_need_no_links(self):
        graph = make_graph([], isolated=("A",))
        request, demand = make_request(destination="A")
        result = make_allocator().allocate(graph, request, demand)
        assert_accepted(self, graph, request, demand, result)
        self.assertEqual(result.path, ["A"])

    def test_missing_endpoints_raise_value_error(self):
        graph = make_graph([("A", "D", 100)])
        for source, destination in (("missing", "D"), ("A", "missing")):
            with self.subTest(source=source, destination=destination):
                request, demand = make_request(source=source, destination=destination)
                with self.assertRaises(ValueError):
                    make_allocator().allocate(graph, request, demand)

    def test_temperature_controls_worse_moves_but_best_route_is_kept(self):
        graph = make_graph([
            ("A", "B", 100), ("B", "D", 100),
            ("A", "C", 50), ("C", "D", 50),
        ])
        request, demand = make_request()
        initial, worse = ["A", "B", "D"], ["A", "C", "D"]
        for temperature, accepts_worse in ((1.0, True), (0.01, False)):
            with self.subTest(temperature=temperature):
                neighbors = Mock(spec=SimulatedAnnealingNeighborGenerator)
                neighbors.generate.side_effect = [worse, None]
                generator = Mock(spec=random.Random)
                generator.random.return_value = 0.5
                config = SimulatedAnnealingConfig(
                    initial_temperature=temperature,
                    minimum_temperature=0.000001,
                    max_iterations=2,
                )
                allocator = make_allocator(
                    config=config, neighbors=neighbors, random_generator=generator
                )
                result = allocator.allocate(graph, request, demand)
                assert_accepted(self, graph, request, demand, result)
                self.assertEqual(result.path, initial)
                self.assertEqual(
                    neighbors.generate.call_args_list[1].kwargs["current_path"],
                    worse if accepts_worse else initial,
                )

    def test_search_stops_at_iteration_or_temperature_limit(self):
        graph = make_graph([("A", "D", 100)])
        request, demand = make_request()
        cases = (
            (SimulatedAnnealingConfig(max_iterations=2), 2),
            (SimulatedAnnealingConfig(
                initial_temperature=1.0, minimum_temperature=0.2,
                cooling_rate=0.5, max_iterations=50,
            ), 3),
        )
        for config, expected_calls in cases:
            with self.subTest(config=config):
                neighbors = Mock(spec=SimulatedAnnealingNeighborGenerator)
                neighbors.generate.return_value = None
                result = make_allocator(config=config, neighbors=neighbors).allocate(
                    graph, request, demand
                )
                assert_accepted(self, graph, request, demand, result)
                self.assertEqual(neighbors.generate.call_count, expected_calls)


if __name__ == "__main__":
    unittest.main()
