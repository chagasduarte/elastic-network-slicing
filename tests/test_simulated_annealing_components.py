"""Analytical checks for SA costs, neighbor generation and configuration."""

import math
import random
import unittest

from algorithms.sa.simulated_annealing_config import SimulatedAnnealingConfig
from algorithms.sa.simulated_annealing_cost_calculator import (
    SimulatedAnnealingCostCalculator,
)
from algorithms.sa.simulated_annealing_neighbor_generator import (
    SimulatedAnnealingNeighborGenerator,
)
from domain.link_allocation import LinkAllocation
from tests.helpers import graph_snapshot, make_graph, make_request


class SimulatedAnnealingCostTests(unittest.TestCase):
    def test_cost_uses_projected_utilization_of_current_period(self):
        graph = make_graph([("A", "B", 100), ("B", "D", 200)], isolated=("C",))
        graph.get_link("A", "B").reserve(LinkAllocation("existing", "t1", 20))
        graph.get_link("B", "D").reserve(LinkAllocation("existing", "t1", 60))
        graph.get_link("A", "B").reserve(LinkAllocation("other-period", "t2", 90))
        _, demand = make_request()
        calculator = SimulatedAnnealingCostCalculator(SimulatedAnnealingConfig())
        before = graph_snapshot(graph)
        cost = calculator.calculate(graph, ["A", "B", "D"], demand)
        # Two of three possible hops; projected utilizations 0.6 and 0.5.
        # Weighted contributions: 0.133333..., 0.165 and 0.21.
        self.assertAlmostEqual(cost, 0.5083333333333333)
        self.assertEqual(graph_snapshot(graph), before)

    def test_cost_rejects_over_capacity_but_allows_exact_capacity(self):
        graph = make_graph([("A", "D", 40)])
        calculator = SimulatedAnnealingCostCalculator(SimulatedAnnealingConfig())
        _, demand = make_request(bandwidth=40)
        self.assertAlmostEqual(calculator.calculate(graph, ["A", "D"], demand), 0.85)
        _, excessive_demand = make_request(bandwidth=41)
        self.assertTrue(math.isinf(
            calculator.calculate(graph, ["A", "D"], excessive_demand)
        ))

    def test_jaccard_cost_counts_undirected_edge_overlap(self):
        graph = make_graph([
            ("A", "B", 100), ("B", "C", 100),
            ("C", "D", 100), ("B", "D", 100),
        ])
        _, demand = make_request()
        calculator = SimulatedAnnealingCostCalculator(SimulatedAnnealingConfig(
            hop_weight=0, avg_utilization_weight=0, bottleneck_weight=0,
            path_change_weight=1,
        ))
        for previous in (["A", "B", "C", "D"], ["D", "C", "B", "A"]):
            with self.subTest(previous=previous):
                # One shared edge among four distinct undirected edges.
                self.assertAlmostEqual(
                    calculator.calculate(graph, ["A", "B", "D"], demand, previous),
                    0.75,
                )
        for previous in (None, ["A", "B", "D"], ["D", "B", "A"]):
            with self.subTest(previous=previous):
                self.assertEqual(
                    calculator.calculate(graph, ["A", "B", "D"], demand, previous),
                    0.0,
                )


class SimulatedAnnealingNeighborTests(unittest.TestCase):
    def generator(self, **config_overrides):
        return SimulatedAnnealingNeighborGenerator(
            SimulatedAnnealingConfig(**config_overrides), random.Random(42)
        )

    def test_neighbor_preserves_endpoints_capacity_and_simple_path(self):
        graph = make_graph([
            ("A", "B", 100), ("B", "D", 100),
            ("A", "C", 100), ("C", "D", 100), ("B", "C", 100),
            ("A", "E", 30), ("E", "D", 30), ("C", "X", 100),
        ])
        _, demand = make_request()
        path = ["A", "B", "D"]
        before = graph_snapshot(graph)
        candidate = self.generator().generate(graph, path, demand)
        self.assertIsNotNone(candidate)
        self.assertNotEqual(candidate, path)
        self.assertEqual(candidate[0], "A")
        self.assertEqual(candidate[-1], "D")
        self.assertEqual(len(candidate), len(set(candidate)))
        self.assertNotIn("E", candidate)
        for link in graph.get_links_from_path(candidate):
            self.assertTrue(link.supports(demand.id, demand.bandwidth))
        self.assertEqual(path, ["A", "B", "D"])
        self.assertEqual(graph_snapshot(graph), before)

    def test_no_neighbor_when_only_original_route_is_viable(self):
        graph = make_graph([
            ("A", "B", 100), ("B", "D", 100),
            ("A", "C", 30), ("C", "D", 30),
        ])
        _, demand = make_request()
        self.assertIsNone(self.generator().generate(graph, ["A", "B", "D"], demand))

    def test_suffix_length_budget_limits_neighbor_search(self):
        graph = make_graph([
            ("A", "B", 100), ("B", "D", 100),
            ("A", "C", 100), ("C", "D", 100),
        ])
        _, demand = make_request()
        self.assertIsNone(self.generator(max_neighbor_steps=1).generate(
            graph, ["A", "B", "D"], demand
        ))
        self.assertEqual(self.generator(max_neighbor_steps=2).generate(
            graph, ["A", "B", "D"], demand
        ), ["A", "C", "D"])


class SimulatedAnnealingConfigTests(unittest.TestCase):
    def test_invalid_temperature_cooling_and_iteration_limits_are_rejected(self):
        cases = {
            "initial_temperature": (0, -1),
            "minimum_temperature": (0, -1),
            "cooling_rate": (0, 1, -0.1, 1.1),
            "max_iterations": (0, -1),
        }
        for field, values in cases.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    with self.assertRaises(ValueError):
                        SimulatedAnnealingConfig(**{field: value})

    def test_cost_weights_must_sum_to_one(self):
        with self.assertRaises(ValueError):
            SimulatedAnnealingConfig(hop_weight=0.9)
        config = SimulatedAnnealingConfig(
            hop_weight=1, avg_utilization_weight=0,
            bottleneck_weight=0, path_change_weight=0,
        )
        self.assertEqual(config.hop_weight, 1)


if __name__ == "__main__":
    unittest.main()
