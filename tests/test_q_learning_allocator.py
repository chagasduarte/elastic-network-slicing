"""Behavioral checks for routing slices with the Q-learning allocator."""

import math
import unittest
from dataclasses import FrozenInstanceError

from algorithms.q_learning.q_learning_allocator import QLearningAllocator
from algorithms.q_learning.q_learning_config import QLearningConfig
from contracts.germany50_topology import create_germany50_graph
from contracts.slice_allocator import SliceAllocator
from domain.link import Link
from domain.link_allocation import LinkAllocation
from domain.network_graph import NetworkGraph
from domain.node import Node
from domain.slice_demand import SliceDemand
from domain.slice_request import SliceRequest
from domain.slice_result import SliceResult
from services.bandwidth_reservation_service import BandwidthReservationService


def make_graph(edges, isolated=()):
    graph = NetworkGraph()
    for name in isolated:
        graph.add_node(Node(name))
    for source, target, capacity in edges:
        graph.add_link(Link(Node(source), Node(target), capacity))
    return graph


def make_request(source="A", destination="D", bandwidth=40, period="t1"):
    demand = SliceDemand(id=period, bandwidth=bandwidth)
    request = SliceRequest(
        id="request-1",
        source=Node(source),
        destination=Node(destination),
        demands=[demand],
    )
    return request, demand


def all_feasible_paths(graph, source, destination, demand):
    """Enumerate small test graphs independently of the learned policy."""
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


def path_cost(graph, path, demand):
    return sum(
        math.exp(demand.bandwidth / link.available_bandwidth_at(demand.id))
        for link in graph.get_links_from_path(path)
    )


class QLearningConfigTests(unittest.TestCase):
    def test_invalid_configuration_is_rejected(self):
        invalid_values = {
            "episodes": (0, -1, 1.5, True),
            "max_steps_per_episode": (0, -1, 1.5, True),
            "learning_rate": (0, -0.1, 1.1, math.nan, math.inf),
            "discount_factor": (-0.1, 1.1, math.nan, math.inf),
            "epsilon_start": (-0.1, 1.1, math.nan, math.inf),
            "epsilon_min": (-0.1, 1.1, math.nan, math.inf),
            "epsilon_decay": (0, -0.1, 1.1, math.nan, math.inf),
            "path_change_penalty": (-0.1, math.nan, math.inf),
        }
        for field, values in invalid_values.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    with self.assertRaises(ValueError):
                        QLearningConfig(**{field: value})

    def test_epsilon_minimum_cannot_exceed_start(self):
        with self.assertRaises(ValueError):
            QLearningConfig(epsilon_start=0.2, epsilon_min=0.3)

    def test_configuration_is_immutable_and_accepts_boundary_values(self):
        config = QLearningConfig(
            episodes=1,
            learning_rate=1,
            discount_factor=0,
            epsilon_start=0,
            epsilon_min=0,
            epsilon_decay=1,
            max_steps_per_episode=1,
            path_change_penalty=0,
        )
        with self.assertRaises(FrozenInstanceError):
            config.episodes = 2


class QLearningAllocatorTests(unittest.TestCase):
    def allocator(self, **overrides):
        return QLearningAllocator(
            config=QLearningConfig(**{"episodes": 500, **overrides}), seed=42
        )

    def assert_valid_result(self, graph, request, demand, result):
        self.assertTrue(result.accepted)
        self.assertEqual(result.request_id, request.id)
        self.assertEqual(result.demand_id, demand.id)
        self.assertEqual(result.bandwidth, demand.bandwidth)
        self.assertEqual(result.path[0], request.source.name)
        self.assertEqual(result.path[-1], request.destination.name)
        self.assertEqual(len(result.path), len(set(result.path)))
        for link in graph.get_links_from_path(result.path):
            self.assertTrue(link.supports(demand.id, demand.bandwidth))

    def assert_rejected(self, result, request, demand):
        self.assertFalse(result.accepted)
        self.assertEqual(result.request_id, request.id)
        self.assertEqual(result.demand_id, demand.id)
        self.assertEqual(result.path, [])
        self.assertEqual(result.bandwidth, 0)

    def test_implements_shared_allocator_contract(self):
        self.assertIsInstance(self.allocator(), SliceAllocator)

    def test_learns_minimum_additive_cost_on_small_graph(self):
        graph = make_graph([
            ("A", "D", 40),
            ("A", "B", 500),
            ("B", "D", 500),
            ("A", "C", 80),
            ("C", "D", 80),
            ("B", "C", 100),
        ])
        request, demand = make_request()
        paths = all_feasible_paths(graph, "A", "D", demand)
        expected_cost = min(path_cost(graph, path, demand) for path in paths)
        result = self.allocator().allocate(graph, request, demand)
        self.assert_valid_result(graph, request, demand, result)
        self.assertAlmostEqual(path_cost(graph, result.path, demand), expected_cost)
        self.assertEqual(result.path, ["A", "B", "D"])

    def test_available_capacity_is_scoped_to_period_and_counts_other_requests(self):
        graph = make_graph([("A", "D", 100)])
        graph.links[0].reserve(LinkAllocation("another-request", "t1", 60))
        allocator = self.allocator()
        for bandwidth, period, accepted in ((40, "t1", True), (41, "t1", False),
                                             (100, "t2", True)):
            with self.subTest(bandwidth=bandwidth, period=period):
                request, demand = make_request(bandwidth=bandwidth, period=period)
                result = allocator.allocate(graph, request, demand)
                if accepted:
                    self.assert_valid_result(graph, request, demand, result)
                else:
                    self.assert_rejected(result, request, demand)

    def test_allocator_does_not_modify_graph_or_reserve_bandwidth(self):
        graph = make_graph([("A", "B", 100), ("B", "D", 100)])
        graph.links[0].reserve(LinkAllocation("existing", "t1", 20))
        nodes_before = graph.nodes
        links_before = [(link.source, link.target, link.capacity,
                         tuple(link.allocations)) for link in graph.links]
        request, demand = make_request()
        result = self.allocator().allocate(graph, request, demand)
        self.assert_valid_result(graph, request, demand, result)
        self.assertEqual(graph.nodes, nodes_before)
        self.assertEqual(
            [(link.source, link.target, link.capacity, tuple(link.allocations))
             for link in graph.links], links_before,
        )

    def test_previous_path_is_preferred_when_change_penalty_outweighs_cost(self):
        graph = make_graph([
            ("A", "B", 100), ("B", "D", 100),
            ("A", "C", 98), ("C", "D", 98),
        ])
        request, demand = make_request()
        previous = SliceResult(request.id, "t0", True, ["A", "C", "D"], 30)
        result = self.allocator().allocate(graph, request, demand, previous)
        self.assert_valid_result(graph, request, demand, result)
        self.assertEqual(result.path, previous.path)
        without_penalty = self.allocator(path_change_penalty=0).allocate(
            graph, request, demand, previous
        )
        self.assertEqual(without_penalty.path, ["A", "B", "D"])

    def test_infeasible_previous_path_does_not_override_capacity(self):
        graph = make_graph([
            ("A", "B", 100), ("B", "D", 100),
            ("A", "C", 30), ("C", "D", 30),
        ])
        request, demand = make_request()
        previous = SliceResult(request.id, "t0", True, ["A", "C", "D"], 20)
        result = self.allocator().allocate(graph, request, demand, previous)
        self.assert_valid_result(graph, request, demand, result)
        self.assertEqual(result.path, ["A", "B", "D"])

    def test_unrelated_or_rejected_previous_result_is_ignored(self):
        graph = make_graph([
            ("A", "B", 100), ("B", "D", 100),
            ("A", "C", 98), ("C", "D", 98),
        ])
        request, demand = make_request()
        cases = (
            SliceResult("another-request", "t0", True, ["A", "C", "D"], 30),
            SliceResult(request.id, "t0", False, ["A", "C", "D"], 0),
            SliceResult(request.id, "t0", True, ["D", "C", "A"], 30),
        )
        for previous in cases:
            with self.subTest(previous=previous):
                result = self.allocator().allocate(graph, request, demand, previous)
                self.assertEqual(result.path, ["A", "B", "D"])

    def test_cycles_and_dead_ends_still_produce_a_simple_route(self):
        graph = make_graph([
            ("A", "B", 100), ("B", "C", 100), ("C", "A", 100),
            ("B", "X", 100), ("C", "D", 100),
        ])
        request, demand = make_request()
        result = self.allocator().allocate(graph, request, demand)
        self.assert_valid_result(graph, request, demand, result)
        self.assertEqual(result.path, ["A", "C", "D"])

    def test_disconnected_destination_and_insufficient_capacity_are_rejected(self):
        graphs = (
            make_graph([("A", "B", 100), ("B", "C", 100), ("C", "A", 100)],
                       isolated=["D"]),
            make_graph([("A", "B", 100), ("B", "D", 39)]),
            make_graph([], isolated=["A", "D"]),
        )
        request, demand = make_request()
        for graph in graphs:
            with self.subTest(graph=graph):
                self.assert_rejected(
                    self.allocator().allocate(graph, request, demand), request, demand
                )

    def test_source_equal_to_destination_needs_no_links(self):
        graph = make_graph([], isolated=["A"])
        request, demand = make_request(destination="A", bandwidth=320)
        result = self.allocator().allocate(graph, request, demand)
        self.assert_valid_result(graph, request, demand, result)
        self.assertEqual(result.path, ["A"])

    def test_missing_endpoints_raise_value_error(self):
        graph = make_graph([("A", "D", 100)])
        for source, destination in (("missing", "D"), ("A", "missing"),
                                    ("missing", "missing")):
            with self.subTest(source=source, destination=destination):
                request, demand = make_request(source=source, destination=destination)
                with self.assertRaises(ValueError):
                    self.allocator().allocate(graph, request, demand)

    def test_new_reservation_and_demand_change_the_next_decision(self):
        graph = make_graph([
            ("A", "B", 100), ("B", "D", 100),
            ("A", "C", 80), ("C", "D", 80),
        ])
        allocator = self.allocator()
        request, demand = make_request()
        first = allocator.allocate(graph, request, demand)
        self.assertEqual(first.path, ["A", "B", "D"])
        BandwidthReservationService().reserve(
            graph.get_links_from_path(first.path),
            LinkAllocation("another-request", demand.id, 80),
        )
        second = allocator.allocate(graph, request, demand, first)
        self.assert_valid_result(graph, request, demand, second)
        self.assertEqual(second.path, ["A", "C", "D"])
        request, larger_demand = make_request(bandwidth=81)
        self.assert_rejected(
            allocator.allocate(graph, request, larger_demand, second),
            request, larger_demand,
        )
        request, next_period = make_request(bandwidth=81, period="t2")
        final = allocator.allocate(graph, request, next_period)
        self.assert_valid_result(graph, request, next_period, final)
        self.assertEqual(final.path, ["A", "B", "D"])

    def test_destination_changes_between_calls(self):
        graph = make_graph([("A", "B", 100), ("B", "D", 100)])
        allocator = self.allocator()
        request, demand = make_request()
        previous = allocator.allocate(graph, request, demand)
        request, demand = make_request(destination="B")
        result = allocator.allocate(graph, request, demand, previous)
        self.assert_valid_result(graph, request, demand, result)
        self.assertEqual(result.path, ["A", "B"])

    def test_same_seed_and_inputs_reproduce_results_and_learning(self):
        graph = make_graph([
            ("A", "B", 100), ("B", "D", 100),
            ("A", "C", 100), ("C", "D", 100),
        ])
        request, demand = make_request()
        first, second = self.allocator(), self.allocator()
        self.assertEqual(first.allocate(graph, request, demand),
                         second.allocate(graph, request, demand))
        self.assertEqual(first.q_table, second.q_table)

    def test_q_table_is_a_defensive_copy_and_resets_for_next_graph(self):
        allocator = self.allocator()
        graph = make_graph([("A", "D", 100)])
        request, demand = make_request()
        allocator.allocate(graph, request, demand)
        snapshot = allocator.q_table
        expected = snapshot["A"]["D"]
        snapshot["A"]["D"] = 12345
        snapshot["injected"] = {}
        self.assertEqual(allocator.q_table["A"]["D"], expected)
        self.assertNotIn("injected", allocator.q_table)
        graph = make_graph([("X", "Y", 100)])
        request, demand = make_request(source="X", destination="Y")
        allocator.allocate(graph, request, demand)
        self.assertNotIn("A", allocator.q_table)
        self.assertIn("X", allocator.q_table)

    def test_step_budget_can_reject_a_feasible_path(self):
        graph = make_graph([("A", "B", 100), ("B", "D", 100)])
        request, demand = make_request()
        result = self.allocator(max_steps_per_episode=1).allocate(
            graph, request, demand
        )
        self.assert_rejected(result, request, demand)
        result = self.allocator(max_steps_per_episode=2).allocate(
            graph, request, demand
        )
        self.assert_valid_result(graph, request, demand, result)

    def test_terminal_transition_updates_value_without_bootstrapping(self):
        graph = make_graph([("A", "D", 100)])
        request, demand = make_request()
        allocator = self.allocator(episodes=1, learning_rate=0.5)
        result = allocator.allocate(graph, request, demand)
        self.assert_valid_result(graph, request, demand, result)
        self.assertAlmostEqual(allocator.q_table["A"]["D"], -0.5 * math.exp(0.4))

    def test_learned_value_includes_discounted_future_cost(self):
        graph = make_graph([("A", "B", 100), ("B", "D", 100)])
        request, demand = make_request()
        allocator = self.allocator(learning_rate=1, discount_factor=0.5)
        result = allocator.allocate(graph, request, demand)
        self.assert_valid_result(graph, request, demand, result)
        self.assertAlmostEqual(allocator.q_table["B"]["D"], -math.exp(0.4))
        self.assertAlmostEqual(allocator.q_table["A"]["B"], -1.5 * math.exp(0.4))

    def test_truncated_transition_preserves_future_cost(self):
        graph = make_graph([("A", "A", 100), ("A", "D", 100)])
        request, demand = make_request()
        allocator = self.allocator(
            learning_rate=1,
            discount_factor=1,
            epsilon_start=1,
            epsilon_min=1,
            epsilon_decay=1,
            max_steps_per_episode=1,
        )
        result = allocator.allocate(graph, request, demand)
        self.assert_valid_result(graph, request, demand, result)
        # Ending the sampling budget at A is not arrival at the destination:
        # the self-loop still owes the cost of subsequently reaching D.
        self.assertAlmostEqual(allocator.q_table["A"]["D"], -math.exp(0.4))
        self.assertAlmostEqual(allocator.q_table["A"]["A"], -2 * math.exp(0.4))

    def test_germany50_uses_existing_scenario_and_external_reservations(self):
        graph = create_germany50_graph()
        demands = [SliceDemand(f"t{index}", bandwidth)
                   for index, bandwidth in enumerate((40, 50, 15, 320), start=1)]
        request = SliceRequest("request-1", Node("A"), Node("L"), demands)
        allocator = QLearningAllocator(seed=42)
        service = BandwidthReservationService()
        previous = None
        for demand in demands:
            with self.subTest(period=demand.id):
                allocations_before = sum(len(link.allocations) for link in graph.links)
                result = allocator.allocate(graph, request, demand, previous)
                self.assert_valid_result(graph, request, demand, result)
                self.assertEqual(sum(len(link.allocations) for link in graph.links),
                                 allocations_before)
                links = graph.get_links_from_path(result.path)
                service.reserve(links, LinkAllocation(request.id, demand.id,
                                                      result.bandwidth))
                for link in links:
                    self.assertEqual(link.allocated_bandwidth_at(demand.id),
                                     demand.bandwidth)
                previous = result


if __name__ == "__main__":
    unittest.main()
