"""Independent, hand-calculated checks of measurements and metric formulas."""

import math
import unittest

from domain.link import Link
from domain.link_allocation import LinkAllocation
from domain.node import Node
from domain.slice_demand import SliceDemand
from domain.slice_request import SliceRequest
from domain.slice_result import SliceResult
from metrics.calculator import MetricsCalculator
from metrics.collector import MetricsCollector
from metrics.models import AlgorithmCounters, ExperimentMetadata
from services.bandwidth_reservation_service import BandwidthReservationService
from tests.helpers import make_graph


class MetricsTests(unittest.TestCase):
    metadata = ExperimentMetadata("fixture", "two-links", "run-1", 42)

    def calculate(self, collector):
        return MetricsCalculator().calculate(collector, self.metadata)

    def record(self, collector, graph, period="t1", bandwidth=40,
               path=("A", "B"), accepted=True, request_id="request-1",
               elapsed=0.0, reserve=True, counters=None,
               source="A", destination="B"):
        demand = SliceDemand(period, bandwidth)
        request = SliceRequest(request_id, Node(source), Node(destination),
                               [demand])
        result = SliceResult(request_id, period, accepted, list(path), bandwidth)
        if accepted and reserve:
            BandwidthReservationService().reserve(
                graph.get_links_from_path(result.path),
                LinkAllocation(request_id, period, bandwidth),
            )
        collector.record(graph, request, demand, result, elapsed, counters)
        return result

    def basic_scenario(self):
        graph = make_graph([("A", "B", 100), ("B", "C", 100)])
        collector = MetricsCollector(["t1"])
        self.record(collector, graph, bandwidth=60, elapsed=1.0)
        self.record(collector, graph, bandwidth=100, accepted=False, path=(),
                    request_id="request-2", elapsed=3.0)
        collector.snapshot_period(graph, "t1")
        return self.calculate(collector)

    def test_acceptance_is_counted_per_demand_and_has_ratio_and_percent(self):
        graph = make_graph([("A", "B", 100)])
        collector = MetricsCollector(["t1", "t2", "t3"])
        for period, accepted in (("t1", True), ("t2", False), ("t3", True)):
            self.record(collector, graph, period=period, accepted=accepted,
                        path=("A", "B") if accepted else ())
            collector.snapshot_period(graph, period)
        metrics = self.calculate(collector).summary.acceptance
        self.assertEqual((metrics.processed, metrics.accepted, metrics.rejected),
                         (3, 2, 1))
        self.assertAlmostEqual(metrics.acceptance_rate, 2 / 3)
        self.assertAlmostEqual(metrics.acceptance_percent, 200 / 3)

    def test_bandwidth_served_uses_actual_end_to_end_allocations(self):
        summary = self.basic_scenario().summary
        self.assertEqual(summary.bandwidth.requested, 160)
        self.assertEqual(summary.bandwidth.allocated, 60)
        self.assertEqual(summary.bandwidth.rejected, 100)
        self.assertEqual(summary.bandwidth.served_ratio, 0.375)
        self.assertEqual(summary.bandwidth.served_percent, 37.5)
        self.assertEqual(summary.acceptance.acceptance_percent, 50)

    def test_multihop_network_consumption_does_not_inflate_delivered_bandwidth(self):
        graph = make_graph([("A", "B", 100), ("B", "C", 100)])
        collector = MetricsCollector(["t1"])
        self.record(collector, graph, bandwidth=30, path=("A", "B", "C"),
                    destination="C")
        collector.snapshot_period(graph, "t1")
        summary = self.calculate(collector).summary
        self.assertEqual(summary.bandwidth.allocated, 30)
        self.assertEqual(summary.network.total_used_bandwidth, 60)
        self.assertEqual(summary.paths.total_hops, 2)

    def test_acceptance_without_reservation_does_not_invent_allocated_bandwidth(self):
        graph = make_graph([("A", "B", 100)])
        collector = MetricsCollector(["t1"])
        self.record(collector, graph, reserve=False)
        collector.snapshot_period(graph, "t1")
        summary = self.calculate(collector).summary
        self.assertEqual(summary.acceptance.accepted, 1)
        self.assertEqual(summary.bandwidth.allocated, 0)
        self.assertEqual(summary.network.total_used_bandwidth, 0)

    def test_other_requests_reservations_are_not_attributed_to_current_demand(self):
        graph = make_graph([("A", "B", 100)])
        graph.links[0].reserve(LinkAllocation("other", "t1", 20))
        collector = MetricsCollector(["t1"])
        self.record(collector, graph, bandwidth=30)
        collector.snapshot_period(graph, "t1")
        summary = self.calculate(collector).summary
        self.assertEqual(summary.bandwidth.allocated, 30)
        self.assertEqual(summary.network.total_used_bandwidth, 50)

    def test_utilization_residual_fairness_and_population_stddev(self):
        network = self.basic_scenario().summary.network
        self.assertEqual(network.physical_capacity, 200)
        self.assertEqual(network.total_capacity, 200)
        self.assertEqual(network.total_used_bandwidth, 60)
        self.assertEqual(network.residual_capacity, 140)
        self.assertEqual(network.average_utilization_percent, 30)
        self.assertEqual(network.weighted_utilization_percent, 30)
        self.assertEqual(network.max_utilization_percent, 60)
        self.assertEqual(network.fairness_jain, 0.5)
        self.assertEqual(network.utilization_stddev, 0.3)
        self.assertEqual(network.saturated_links, 0)

    def test_mean_utilization_and_capacity_weighted_utilization_are_distinct(self):
        graph = make_graph([("A", "B", 100), ("B", "C", 300)])
        collector = MetricsCollector(["t1"])
        self.record(collector, graph, bandwidth=100)
        collector.snapshot_period(graph, "t1")
        network = self.calculate(collector).summary.network
        self.assertEqual(network.average_utilization_percent, 50)
        self.assertEqual(network.weighted_utilization_percent, 25)
        self.assertEqual(network.residual_capacity, 300)

    def test_all_links_equally_used_have_unit_jain_and_zero_stddev(self):
        graph = make_graph([("A", "B", 100), ("B", "C", 100)])
        collector = MetricsCollector(["t1"])
        self.record(collector, graph, bandwidth=40, path=("A", "B", "C"),
                    destination="C")
        collector.snapshot_period(graph, "t1")
        network = self.calculate(collector).summary.network
        self.assertAlmostEqual(network.fairness_jain, 1.0)
        self.assertEqual(network.utilization_stddev, 0)

    def test_idle_links_are_included_in_jain_and_all_zero_is_defined(self):
        graph = make_graph([("A", "B", 100), ("B", "C", 100)])
        collector = MetricsCollector(["t1"])
        collector.snapshot_period(graph, "t1")
        network = self.calculate(collector).summary.network
        self.assertEqual(network.link_count, 2)
        self.assertEqual(network.fairness_jain, 0)
        self.assertEqual(network.utilization_stddev, 0)
        self.assertEqual(network.residual_capacity, 200)
        self.assertEqual(network.average_utilization_percent, 0)

    def test_exactly_saturated_link_is_counted(self):
        graph = make_graph([("A", "B", 100), ("B", "C", 100)])
        collector = MetricsCollector(["t1"])
        self.record(collector, graph, bandwidth=100)
        collector.snapshot_period(graph, "t1")
        network = self.calculate(collector).summary.network
        self.assertEqual(network.saturated_links, 1)
        self.assertEqual(network.saturated_link_periods, 1)
        self.assertEqual(network.max_utilization_percent, 100)
        self.assertEqual(network.residual_capacity, 100)

    def test_undirected_reversed_paths_and_duplicate_reference_count_capacity_once(self):
        graph = make_graph([("B", "A", 100)])
        graph.add_link(graph.links[0])
        collector = MetricsCollector(["t1"])
        self.record(collector, graph, bandwidth=40)
        collector.snapshot_period(graph, "t1")
        network = self.calculate(collector).summary.network
        self.assertEqual(network.link_count, 1)
        self.assertEqual(network.total_capacity, 100)
        self.assertEqual(network.total_used_bandwidth, 40)

    def test_mirrored_undirected_links_do_not_duplicate_capacity_or_allocations(self):
        for mirror_has_allocation in (False, True):
            with self.subTest(mirror_has_allocation=mirror_has_allocation):
                graph = make_graph([("A", "B", 100), ("B", "A", 100)])
                collector = MetricsCollector(["t1"])
                self.record(collector, graph, bandwidth=40)
                if mirror_has_allocation:
                    graph.links[1].reserve(LinkAllocation("request-1", "t1", 40))
                collector.snapshot_period(graph, "t1")
                network = self.calculate(collector).summary.network
                self.assertEqual(network.total_capacity, 100)
                self.assertEqual(network.total_used_bandwidth, 40)
                self.assertEqual(network.link_count, 1)

    def test_conflicting_mirrored_links_are_rejected_instead_of_guessed(self):
        for graph in (
            make_graph([("A", "B", 100), ("B", "A", 200)]),
            make_graph([("A", "B", 100), ("B", "A", 100)]),
        ):
            if graph.links[0].capacity == graph.links[1].capacity:
                graph.links[0].reserve(LinkAllocation("first", "t1", 10))
                graph.links[1].reserve(LinkAllocation("second", "t1", 20))
            with self.subTest(graph=graph), self.assertRaises(ValueError):
                MetricsCollector(["t1"]).snapshot_period(graph, "t1")

    def test_paths_count_only_valid_accepted_routes_and_use_nodes_minus_one(self):
        graph = make_graph([("A", "B", 100), ("B", "C", 100),
                            ("A", "C", 100)])
        collector = MetricsCollector(["t1"])
        for index, (accepted, path, destination) in enumerate((
            (True, ("A", "B"), "B"),
            (True, ("A", "B", "C"), "C"),
            (False, ("A", "C"), "C"),
            (True, (), "C"),
            (True, ("A", "missing", "C"), "C"),
            (True, ("B", "C"), "C"),
            (True, ("A", "B", "A", "C"), "C"),
        )):
            self.record(collector, graph, path=path, accepted=accepted,
                        destination=destination, reserve=False,
                        request_id=f"request-{index}")
        collector.snapshot_period(graph, "t1")
        paths = self.calculate(collector).summary.paths
        self.assertEqual(paths.accepted_paths, 2)
        self.assertEqual(paths.mean_hops, 1.5)
        self.assertEqual((paths.min_hops, paths.max_hops, paths.total_hops),
                         (1, 2, 3))

    def test_same_node_path_is_valid_with_zero_hops(self):
        graph = make_graph([], isolated=["A"])
        collector = MetricsCollector(["t1"])
        self.record(collector, graph, path=("A",), destination="A")
        collector.snapshot_period(graph, "t1")
        paths = self.calculate(collector).summary.paths
        self.assertEqual(paths.accepted_paths, 1)
        self.assertEqual(paths.mean_hops, 0)
        self.assertEqual(paths.total_hops, 0)

    def test_timing_uses_population_stddev_in_seconds(self):
        timing = self.basic_scenario().summary.timing
        self.assertEqual(timing.total_seconds, 4)
        self.assertEqual(timing.mean_seconds, 2)
        self.assertEqual(timing.min_seconds, 1)
        self.assertEqual(timing.max_seconds, 3)
        self.assertEqual(timing.stddev_seconds, 1)

    def test_periods_have_independent_reservations_metrics_and_demand_order(self):
        graph = make_graph([("A", "B", 100)])
        collector = MetricsCollector(["t2", "t10"])
        self.record(collector, graph, period="t2", bandwidth=100, elapsed=2)
        collector.snapshot_period(graph, "t2")
        self.record(collector, graph, period="t10", bandwidth=50, elapsed=3)
        collector.snapshot_period(graph, "t10")
        result = self.calculate(collector)
        self.assertEqual([item.period for item in result.periods], ["t2", "t10"])
        first, second = (item.metrics for item in result.periods)
        self.assertEqual(first.network.total_used_bandwidth, 100)
        self.assertEqual(second.network.total_used_bandwidth, 50)
        self.assertEqual(second.network.residual_capacity, 50)
        self.assertEqual(first.bandwidth.requested, 100)
        self.assertEqual(second.bandwidth.requested, 50)
        self.assertEqual(first.timing.total_seconds, 2)
        self.assertEqual(second.timing.total_seconds, 3)
        self.assertEqual(first.path_changes.comparable_transitions, 0)
        self.assertEqual(second.path_changes.reused, 1)

    def test_general_network_summary_uses_link_period_samples(self):
        graph = make_graph([("A", "B", 100)])
        collector = MetricsCollector(["t1", "t2", "t3"])
        for period, bandwidth in (("t1", 100), ("t2", 100), ("t3", 50)):
            self.record(collector, graph, period=period, bandwidth=bandwidth)
            collector.snapshot_period(graph, period)
        network = self.calculate(collector).summary.network
        self.assertEqual(network.physical_capacity, 100)
        self.assertEqual(network.total_capacity, 300)
        self.assertEqual(network.total_used_bandwidth, 250)
        self.assertEqual(network.residual_capacity, 50)
        self.assertEqual(network.link_count, 1)
        self.assertEqual(network.link_period_count, 3)
        self.assertEqual(network.saturated_links, 1)
        self.assertEqual(network.saturated_link_periods, 2)
        self.assertAlmostEqual(network.average_utilization_percent, 250 / 3)
        self.assertAlmostEqual(network.fairness_jain, 25 / 27)
        self.assertAlmostEqual(network.utilization_stddev, math.sqrt(1 / 18))

    def test_saturation_thresholds_80_90_and_100(self):
        graph = make_graph([("A", "B", 100), ("B", "C", 100), ("C", "D", 100),
                            ("D", "E", 100)])
        collector = MetricsCollector(["t1"])
        for index, (path, bandwidth) in enumerate(
            ((("A", "B"), 79), (("B", "C"), 80), (("C", "D"), 90), (("D", "E"), 100))
        ):
            self.record(collector, graph, bandwidth=bandwidth, path=path,
                        request_id=f"r{index}", source=path[0], destination=path[1])
        collector.snapshot_period(graph, "t1")
        network = self.calculate(collector).summary.network
        self.assertEqual(network.saturated_links_80, 3)
        self.assertEqual(network.saturated_links_90, 2)
        self.assertEqual(network.saturated_links, 1)
        self.assertEqual(network.saturated_link_periods_80, 3)
        self.assertEqual(network.saturated_link_periods_90, 2)

    def test_jain_is_computed_per_period_and_averaged(self):
        graph = make_graph([("A", "B", 100), ("B", "C", 100)])
        collector = MetricsCollector(["t1", "t2"])
        # t1: um enlace a 100%, outro ocioso -> Jain 1/2. t2: ambos a 50% -> Jain 1.
        self.record(collector, graph, period="t1", bandwidth=100)
        collector.snapshot_period(graph, "t1")
        self.record(collector, graph, period="t2", bandwidth=50)
        self.record(collector, graph, period="t2", bandwidth=50, path=("B", "C"),
                    request_id="request-2", source="B", destination="C")
        collector.snapshot_period(graph, "t2")
        result = self.calculate(collector)
        first, second = (item.metrics.network for item in result.periods)
        self.assertAlmostEqual(first.fairness_jain, 0.5)
        self.assertAlmostEqual(second.fairness_jain, 1.0)
        self.assertAlmostEqual(result.summary.network.fairness_jain_period_mean, 0.75)

    def test_reuse_change_rejection_gap_and_request_identity(self):
        graph = make_graph([("A", "B", 100), ("B", "C", 100),
                            ("A", "C", 100)])
        periods = [f"t{index}" for index in range(1, 8)]
        collector = MetricsCollector(periods)
        scenarios = (("t1", ("A", "C"), True),
                     ("t2", ("A", "C"), True),
                     ("t3", ("A", "B", "C"), True),
                     ("t4", (), False),
                     ("t5", ("A", "C"), True),
                     ("t7", ("A", "C"), True))
        for period, path, accepted in scenarios:
            self.record(collector, graph, period=period, path=path,
                        accepted=accepted, destination="C")
        self.record(collector, graph, period="t6", path=("A", "C"),
                    destination="C", request_id="different")
        for period in periods:
            collector.snapshot_period(graph, period)
        result = self.calculate(collector)
        changes = result.summary.path_changes
        self.assertEqual(changes.comparable_transitions, 2)
        self.assertEqual((changes.reused, changes.changed), (1, 1))
        self.assertEqual(changes.reuse_rate, 0.5)
        self.assertEqual(changes.change_rate, 0.5)
        by_period = {item.period: item.metrics for item in result.periods}
        self.assertEqual(by_period["t3"].path_changes.changed, 1)
        self.assertEqual(by_period["t7"].path_changes.comparable_transitions, 0)

    def test_invalid_previous_path_breaks_reuse_comparison(self):
        graph = make_graph([("A", "B", 100)])
        collector = MetricsCollector(["t1", "t2", "t3"])
        for period, path in (("t1", ("A", "B")), ("t2", ()),
                             ("t3", ("A", "B"))):
            self.record(collector, graph, period=period, path=path, reserve=False)
            collector.snapshot_period(graph, period)
        self.assertEqual(self.calculate(collector).summary.path_changes.
                         comparable_transitions, 0)

    def test_empty_experiment_has_finite_zero_metrics_without_division_by_zero(self):
        collector = MetricsCollector([])
        result = self.calculate(collector)
        self.assertEqual(result.periods, ())
        self.assertEqual(result.summary.acceptance.processed, 0)
        self.assertEqual(result.summary.acceptance.acceptance_rate, 0)
        self.assertEqual(result.summary.bandwidth.served_ratio, 0)
        self.assertEqual(result.summary.network.fairness_jain, 0)
        self.assertEqual(result.summary.network.utilization_stddev, 0)
        self.assertEqual(result.summary.paths.mean_hops, 0)
        self.assertEqual(result.summary.paths.min_hops, 0)
        self.assertEqual(result.summary.paths.max_hops, 0)
        self.assertEqual(result.summary.timing.mean_seconds, 0)
        self.assertEqual(result.summary.timing.min_seconds, 0)
        self.assertEqual(result.summary.timing.max_seconds, 0)
        self.assertEqual(result.summary.timing.stddev_seconds, 0)
        self.assertEqual(result.summary.path_changes.reuse_rate, 0)
        self.assertEqual(result.summary.path_changes.change_rate, 0)

    def test_all_rejected_demands_leave_network_idle_and_paths_empty(self):
        graph = make_graph([("A", "B", 100)])
        collector = MetricsCollector(["t1"])
        self.record(collector, graph, bandwidth=101, accepted=False, path=())
        self.record(collector, graph, bandwidth=200, accepted=False, path=(),
                    request_id="second")
        collector.snapshot_period(graph, "t1")
        summary = self.calculate(collector).summary
        self.assertEqual(summary.acceptance.rejected, 2)
        self.assertEqual(summary.acceptance.acceptance_rate, 0)
        self.assertEqual(summary.bandwidth.rejected, 301)
        self.assertEqual(summary.bandwidth.served_percent, 0)
        self.assertEqual(summary.network.total_used_bandwidth, 0)
        self.assertEqual(summary.network.residual_capacity, 100)
        self.assertEqual(summary.paths.accepted_paths, 0)
        self.assertEqual(summary.paths.mean_hops, 0)

    def test_measurements_and_network_snapshots_are_independent_of_later_mutations(self):
        graph = make_graph([("A", "B", 100)])
        collector = MetricsCollector(["t1"])
        result = self.record(collector, graph, bandwidth=40)
        collector.snapshot_period(graph, "t1")
        result.path.append("unrelated")
        graph.links[0].allocations.clear()
        self.assertIsInstance(collector.measurements, tuple)
        self.assertIsInstance(collector.network_snapshots, tuple)
        summary = self.calculate(collector).summary
        self.assertEqual(collector.measurements[0].path, ("A", "B"))
        self.assertEqual(summary.network.total_used_bandwidth, 40)
        self.assertEqual(summary.bandwidth.allocated, 40)

    def test_missing_counters_are_unavailable_not_zero(self):
        counters = self.basic_scenario().summary.counters
        self.assertIsNone(counters.path_search_attempts)
        self.assertIsNone(counters.paths_evaluated)
        self.assertIsNone(counters.iterations)
        self.assertIsNone(counters.nodes_visited)

    def test_available_counters_sum_and_missing_observations_remain_unavailable(self):
        graph = make_graph([("A", "B", 100)])
        collector = MetricsCollector(["t1", "t2"])
        for period, counters in (("t1", AlgorithmCounters(
            path_search_attempts=2, paths_evaluated=1, iterations=3,
            extra={"episodes": 4})), ("t2", AlgorithmCounters(
            path_search_attempts=5, paths_evaluated=0,
            extra={"episodes": 6}))):
            self.record(collector, graph, period=period, counters=counters)
            collector.snapshot_period(graph, period)
        result = self.calculate(collector)
        counters = result.summary.counters
        self.assertEqual(counters.path_search_attempts, 7)
        self.assertEqual(counters.paths_evaluated, 1)
        self.assertIsNone(counters.iterations)
        self.assertIsNone(counters.nodes_visited)
        self.assertEqual(counters.extra["episodes"], 10)
        self.assertEqual(result.periods[0].metrics.counters.iterations, 3)


if __name__ == "__main__":
    unittest.main()
