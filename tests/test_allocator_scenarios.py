"""Run the existing allocators through the shared reservation workflow."""

import unittest

from contracts.create_topo import create_test_graph
from contracts.germany50_topology import create_germany50_graph
from domain.link_allocation import LinkAllocation
from domain.node import Node
from domain.slice_demand import SliceDemand
from domain.slice_request import SliceRequest
from main import create_allocator
from services.bandwidth_reservation_service import BandwidthReservationService
from tests.helpers import assert_accepted, assert_rejected, graph_snapshot


class AllocatorScenarioTests(unittest.TestCase):
    def run_periods(self, algorithm, graph, bandwidths, expected_acceptance):
        demands = [
            SliceDemand(f"t{index}", bandwidth)
            for index, bandwidth in enumerate(bandwidths, start=1)
        ]
        request = SliceRequest("request-1", Node("A"), Node("L"), demands)
        service = BandwidthReservationService()
        allocator = create_allocator(algorithm, service, seed=42)
        previous = None

        for demand, expected in zip(demands, expected_acceptance):
            with self.subTest(algorithm=algorithm, period=demand.id):
                before = graph_snapshot(graph)
                result = allocator.allocate(graph, request, demand, previous)
                self.assertEqual(graph_snapshot(graph), before)
                if expected:
                    assert_accepted(self, graph, request, demand, result)
                    links = graph.get_links_from_path(result.path)
                    service.reserve(
                        links,
                        LinkAllocation(result.request_id, result.demand_id,
                                       result.bandwidth),
                    )
                    for link in links:
                        self.assertEqual(
                            link.allocated_bandwidth_at(demand.id),
                            demand.bandwidth,
                        )
                    self.assertEqual(
                        sum(link.allocated_bandwidth_at(demand.id)
                            for link in graph.links),
                        len(links) * demand.bandwidth,
                    )
                else:
                    assert_rejected(self, request, demand, result)
                    self.assertTrue(all(
                        link.allocated_bandwidth_at(demand.id) == 0
                        for link in graph.links
                    ))
                previous = result

    def test_germany50_with_the_four_original_demands(self):
        for algorithm in ("petic", "aco", "sa"):
            self.run_periods(
                algorithm, create_germany50_graph(),
                (40, 50, 15, 320), (True, True, True, True),
            )

    def test_elastic_demands_include_rejection_and_recovery(self):
        for algorithm in ("petic", "aco", "sa"):
            self.run_periods(
                algorithm, create_test_graph(),
                (40, 50, 15, 320, 321, 40),
                (True, True, True, True, False, True),
            )


if __name__ == "__main__":
    unittest.main()
