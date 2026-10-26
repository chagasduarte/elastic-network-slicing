"""Contratos de exportação e estatísticas entre repetições."""

import csv
from dataclasses import asdict, replace
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from metrics.aggregation import aggregate_runs
from metrics.exporter import MetricsExporter
from metrics.models import (
    AcceptanceMetrics, AlgorithmCounters, BandwidthMetrics, DemandMeasurement,
    ExperimentMetadata, ExperimentMetrics, LinkMeasurement, MetricSummary,
    NetworkMetrics, NetworkSnapshot, PathChangeMetrics, PathMetrics, PeriodMetrics,
    TimingMetrics,
)


def make_run(run_id="1", seed=42, accepted=True, elapsed=1.0):
    allocated = 40.0 if accepted else 0.0
    counters = AlgorithmCounters()
    summary = MetricSummary(
        acceptance=AcceptanceMetrics(1, int(accepted), int(not accepted), float(accepted), 100.0 * accepted),
        bandwidth=BandwidthMetrics(40.0, allocated, 40.0 - allocated, float(accepted), 100.0 * accepted),
        network=NetworkMetrics(100.0, 100.0, allocated, 100.0 - allocated, 1, 1,
                               allocated, allocated, allocated, 0, 0, float(accepted), 0.0),
        paths=PathMetrics(int(accepted), float(accepted), int(accepted), int(accepted), int(accepted)),
        timing=TimingMetrics(elapsed, elapsed, elapsed, elapsed, 0.0),
        path_changes=PathChangeMetrics(0, 0, 0, 0.0, 0.0),
        counters=counters,
    )
    return ExperimentMetrics(
        metadata=ExperimentMetadata("aco", "teste", run_id, seed, {"iterations": 20}, "cenário-1"),
        summary=summary,
        periods=(PeriodMetrics("t1", summary),),
        measurements=(DemandMeasurement(
            "request-1", "t1", "A", "B", 40.0, allocated, accepted,
            ("A", "B") if accepted else (), accepted, elapsed, counters,
        ),),
        network_snapshots=(NetworkSnapshot("t1", (LinkMeasurement("A", "B", 100.0, allocated),)),),
        period_order=("t1",),
    )


class MetricsExporterTests(unittest.TestCase):
    def test_json_roundtrip_preserves_metadata_samples_snapshots_and_nulls(self):
        run = make_run()
        aggregates = aggregate_runs([run])
        with TemporaryDirectory() as temporary:
            path = MetricsExporter.export_json([run], Path(temporary) / "nested/results.json", aggregates)
            payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["runs"], json.loads(json.dumps([asdict(run)])))
        self.assertEqual(payload["aggregates"], aggregates)
        self.assertIsNone(payload["runs"][0]["summary"]["counters"]["iterations"])
        self.assertEqual(payload["runs"][0]["measurements"][0]["path"], ["A", "B"])
        self.assertEqual(payload["runs"][0]["network_snapshots"][0]["links"][0]["used_bandwidth"], 40.0)

    def test_csv_has_summary_and_period_rows_for_each_run(self):
        runs = [make_run(), make_run("2", 43, False, 3.0)]
        with TemporaryDirectory() as temporary:
            path = MetricsExporter.export_csv(iter(runs), Path(temporary) / "nested/runs.csv")
            with path.open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 4)
        self.assertEqual([row["scope"] for row in rows], ["summary", "period"] * 2)
        self.assertEqual([row["period"] for row in rows], ["", "t1"] * 2)
        self.assertEqual(rows[0]["algorithm"], "aco")
        self.assertEqual(rows[0]["topology"], "teste")
        self.assertEqual(rows[0]["run_id"], "1")
        self.assertEqual(rows[0]["seed"], "42")
        self.assertEqual(rows[0]["scenario_id"], "cenário-1")
        self.assertEqual(json.loads(rows[0]["parameters"]), {"iterations": 20})
        self.assertEqual(float(rows[0]["acceptance.acceptance_percent"]), 100.0)
        self.assertEqual(float(rows[2]["acceptance.acceptance_percent"]), 0.0)
        self.assertEqual(rows[0]["counters.iterations"], "")

    def test_aggregate_csv_preserves_group_metadata_and_statistics(self):
        aggregates = aggregate_runs([make_run(), make_run("2", 43, False, 3.0)])
        with TemporaryDirectory() as temporary:
            path = MetricsExporter.export_aggregates_csv(aggregates, Path(temporary) / "aggregate.csv")
            with path.open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 2)
        self.assertEqual(json.loads(rows[0]["run_ids"]), ["1", "2"])
        self.assertEqual(json.loads(rows[0]["seeds"]), [42, 43])
        self.assertEqual(float(rows[0]["acceptance.acceptance_percent.mean"]), 50.0)
        self.assertEqual(float(rows[0]["timing.total_seconds.stddev"]), 1.0)
        self.assertEqual(rows[0]["counters.iterations.mean"], "")
        self.assertEqual(rows[0]["counters.iterations.count"], "0")

    def test_empty_exports_and_terminal_are_valid(self):
        with TemporaryDirectory() as temporary:
            json_path = MetricsExporter.export_json([], Path(temporary) / "empty.json")
            csv_path = MetricsExporter.export_csv([], Path(temporary) / "empty.csv")
            self.assertEqual(json.loads(json_path.read_text())["runs"], [])
            with csv_path.open(newline="") as stream:
                reader = csv.DictReader(stream)
                self.assertEqual(list(reader), [])
                self.assertIn("algorithm", reader.fieldnames)
        self.assertIn("Nenhuma execução", MetricsExporter.format_terminal([]))

    def test_terminal_identifies_runs_periods_and_aggregate(self):
        runs = [make_run()]
        output = MetricsExporter.format_terminal(runs, aggregate_runs(runs))
        for text in ("aco", "teste", "execução 1", "seed=42", "cenário-1", "t1:", "100.00%", "n=1"):
            self.assertIn(text, output)


class MetricsAggregationTests(unittest.TestCase):
    def test_numeric_statistics_use_population_deviation_and_record_seeds(self):
        aggregates = aggregate_runs([make_run(), make_run("2", 43, False, 3.0)])
        summary, period = aggregates
        expected = {"count": 2, "mean": 50.0, "median": 50.0, "min": 0.0, "max": 100.0, "stddev": 50.0}
        self.assertEqual(summary["metrics"]["acceptance.acceptance_percent"], expected)
        self.assertEqual(summary["metrics"]["timing.total_seconds"], {
            "count": 2, "mean": 2.0, "median": 2.0, "min": 1.0, "max": 3.0, "stddev": 1.0,
        })
        self.assertEqual(summary["run_ids"], ["1", "2"])
        self.assertEqual(summary["seeds"], [42, 43])
        self.assertIsNone(summary["period"])
        self.assertEqual(period["period"], "t1")
        self.assertEqual(period["metrics"]["acceptance.acceptance_percent"], expected)

    def test_unavailable_counters_remain_unavailable(self):
        group = aggregate_runs([make_run()])[0]
        self.assertEqual(group["metrics"]["counters.iterations"], {
            "count": 0, "mean": None, "median": None, "min": None, "max": None, "stddev": None,
        })
        self.assertEqual(group["metrics"]["acceptance.accepted"]["stddev"], 0.0)

    def test_optional_counters_count_only_available_observations(self):
        first = make_run()
        second = make_run("2", 43)
        second = replace(second, summary=replace(second.summary, counters=AlgorithmCounters(
            iterations=5, extra={"custom_searches": 2},
        )))
        summary = aggregate_runs([first, second])[0]
        self.assertEqual(summary["metrics"]["counters.iterations"]["count"], 1)
        self.assertEqual(summary["metrics"]["counters.iterations"]["mean"], 5)
        self.assertEqual(summary["metrics"]["counters.extra.custom_searches"]["count"], 1)

    def test_groups_do_not_mix_algorithms_topologies_scenarios_or_parameters(self):
        original = make_run()
        variants = [original]
        for field, value in (("algorithm", "petic"), ("topology", "other"),
                             ("scenario_id", "other"), ("parameters", {"iterations": 30})):
            variants.append(replace(original, metadata=replace(original.metadata, **{field: value})))
        aggregates = aggregate_runs(variants)
        self.assertEqual(len(aggregates), 10)
        self.assertTrue(all(group["run_count"] == 1 for group in aggregates))
        self.assertTrue(all("seed" not in group["metrics"] for group in aggregates))

    def test_parameter_dictionary_order_does_not_split_groups(self):
        first = make_run()
        first = replace(first, metadata=replace(first.metadata, parameters={"a": 1, "b": 2}))
        second = replace(first, metadata=replace(first.metadata, parameters={"b": 2, "a": 1}, run_id="2"))
        self.assertEqual(aggregate_runs([first, second])[0]["run_count"], 2)

    def test_empty_runs_have_no_aggregates(self):
        self.assertEqual(aggregate_runs([]), [])


if __name__ == "__main__":
    unittest.main()
