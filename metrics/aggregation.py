"""Estatísticas de repetições comparáveis, sem misturar cenários ou parâmetros."""

from collections import defaultdict
from dataclasses import asdict
import json
from statistics import mean, median
from typing import Any, Iterable

from metrics.intervals import confidence_interval_95, sample_stddev
from metrics.models import ExperimentMetrics


def flatten_metrics(values: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Preserva nomes das categorias ao converter métricas para colunas."""
    flattened = {}
    for name, value in values.items():
        key = f"{prefix}.{name}" if prefix else name
        if isinstance(value, dict):
            flattened.update(flatten_metrics(value, key))
        else:
            flattened[key] = value
    return flattened


def aggregate_runs(runs: Iterable[ExperimentMetrics]) -> list[dict[str, Any]]:
    """Agrupa por algoritmo, topologia, cenário, parâmetros e período.

    ``period=None`` representa o resumo geral. ``stddev`` é o desvio-padrão
    amostral (n - 1) e ``ci95_low``/``ci95_high`` o intervalo de confiança de
    95% da média (t de Student); ambos são None com menos de 2 observações.
    Valores indisponíveis não são convertidos em zero nem usados
    como observações: cada métrica informa seu próprio ``count``.
    """
    groups = {}
    observations = defaultdict(list)
    for run in runs:
        metadata = run.metadata
        parameters_key = json.dumps(metadata.parameters, sort_keys=True, allow_nan=False)
        summaries = [(None, run.summary)]
        summaries.extend((period.period, period.metrics) for period in run.periods)
        for period, summary in summaries:
            key = (
                metadata.algorithm, metadata.topology, metadata.scenario_id,
                parameters_key, period,
            )
            if key not in groups:
                groups[key] = {
                    "algorithm": metadata.algorithm,
                    "topology": metadata.topology,
                    "scenario_id": metadata.scenario_id,
                    "parameters": json.loads(parameters_key),
                    "period": period,
                    "run_count": 0,
                    "run_ids": [],
                    "seeds": [],
                    "metrics": {},
                }
            group = groups[key]
            group["run_count"] += 1
            group["run_ids"].append(metadata.run_id)
            group["seeds"].append(metadata.seed)
            observations[key].append(flatten_metrics(asdict(summary)))

    for key, group in groups.items():
        samples = observations[key]
        metric_names = sorted({name for sample in samples for name in sample})
        for name in metric_names:
            values = [
                sample[name] for sample in samples
                if isinstance(sample.get(name), (int, float))
                and not isinstance(sample[name], bool)
            ]
            interval = confidence_interval_95(values)
            group["metrics"][name] = {
                "count": len(values),
                "mean": mean(values) if values else None,
                "median": median(values) if values else None,
                "min": min(values) if values else None,
                "max": max(values) if values else None,
                "stddev": sample_stddev(values),
                "ci95_low": interval[0] if interval else None,
                "ci95_high": interval[1] if interval else None,
            }
    return list(groups.values())
