"""Exportação de resultados com a biblioteca padrão do Python."""

import csv
from dataclasses import asdict
import json
from pathlib import Path
from typing import Any, Iterable

from metrics.aggregation import flatten_metrics
from metrics.models import ExperimentMetrics


class MetricsExporter:
    """Converte resultados; escrita e formatação ficam fora do tempo medido."""

    @staticmethod
    def export_json(
        runs: Iterable[ExperimentMetrics],
        path: str | Path,
        aggregates: list[dict[str, Any]] | None = None,
    ) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "runs": [asdict(run) for run in runs],
            "aggregates": aggregates if aggregates is not None else [],
        }
        target.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        return target

    @staticmethod
    def export_csv(runs: Iterable[ExperimentMetrics], path: str | Path) -> Path:
        rows = []
        for run in runs:
            metadata = asdict(run.metadata)
            metadata["parameters"] = json.dumps(
                metadata["parameters"], sort_keys=True, ensure_ascii=False, allow_nan=False,
            )
            summaries = [(None, run.summary)]
            summaries.extend((period.period, period.metrics) for period in run.periods)
            for period, summary in summaries:
                rows.append({
                    **metadata,
                    "scope": "summary" if period is None else "period",
                    "period": period,
                    **flatten_metrics(asdict(summary)),
                })
        fields = [
            "algorithm", "topology", "run_id", "seed", "scenario_id", "parameters",
            "scope", "period",
        ]
        return MetricsExporter._write_csv(rows, path, fields)

    @staticmethod
    def export_aggregates_csv(
        aggregates: Iterable[dict[str, Any]], path: str | Path,
    ) -> Path:
        rows = []
        for aggregate in aggregates:
            row = {name: value for name, value in aggregate.items() if name != "metrics"}
            for name in ("parameters", "run_ids", "seeds"):
                row[name] = json.dumps(
                    row[name], sort_keys=True, ensure_ascii=False, allow_nan=False,
                )
            row["scope"] = "summary" if row["period"] is None else "period"
            row.update(flatten_metrics(aggregate["metrics"]))
            rows.append(row)
        fields = [
            "algorithm", "topology", "scenario_id", "parameters", "scope", "period",
            "run_count", "run_ids", "seeds",
        ]
        return MetricsExporter._write_csv(rows, path, fields)

    @staticmethod
    def _write_csv(
        rows: list[dict[str, Any]], path: str | Path, leading_fields: list[str],
    ) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        extra_fields = sorted({name for row in rows for name in row} - set(leading_fields))
        with target.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=leading_fields + extra_fields)
            writer.writeheader()
            writer.writerows(rows)
        return target

    @staticmethod
    def format_terminal(
        runs: Iterable[ExperimentMetrics],
        aggregates: list[dict[str, Any]] | None = None,
    ) -> str:
        lines = ["Resumo dos experimentos (tempos somente de allocate):"]
        found = False
        for run in runs:
            found = True
            metadata = run.metadata
            lines.append(
                f"{metadata.algorithm} | {metadata.topology} | execução {metadata.run_id} "
                f"| seed={metadata.seed} | cenário={metadata.scenario_id}"
            )
            summaries = [("geral", run.summary)]
            summaries.extend((period.period, period.metrics) for period in run.periods)
            for period, metrics in summaries:
                lines.append(
                    f"  {period}: aceitas {metrics.acceptance.accepted}/{metrics.acceptance.processed} "
                    f"({metrics.acceptance.acceptance_percent:.2f}%) | "
                    f"banda {metrics.bandwidth.allocated:g}/{metrics.bandwidth.requested:g} Mbps | "
                    f"utilização média {metrics.network.average_utilization_percent:.2f}% | "
                    f"Jain {metrics.network.fairness_jain:.4f} | "
                    f"saltos {metrics.paths.mean_hops:.2f} | "
                    f"tempo {metrics.timing.total_seconds:.6f} s"
                )
        if not found:
            lines.append("Nenhuma execução.")
        if aggregates:
            lines.append("Agregação das repetições (média ± desvio-padrão populacional):")
            for aggregate in aggregates:
                if aggregate["period"] is not None:
                    continue
                acceptance = aggregate["metrics"]["acceptance.acceptance_percent"]
                timing = aggregate["metrics"]["timing.total_seconds"]
                lines.append(
                    f"  {aggregate['algorithm']} | {aggregate['topology']} "
                    f"| cenário={aggregate['scenario_id']} | n={aggregate['run_count']}: "
                    f"aceitação {acceptance['mean']:.2f} ± {acceptance['stddev']:.2f}% | "
                    f"tempo {timing['mean']:.6f} ± {timing['stddev']:.6f} s"
                )
        return "\n".join(lines)
