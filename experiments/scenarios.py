"""Cenários de demanda elástica: requisições sorteadas por semente."""

from dataclasses import dataclass
import json
from pathlib import Path
import random

from domain.network_graph import NetworkGraph
from domain.node import Node
from domain.slice_demand import SliceDemand
from domain.slice_request import SliceRequest


@dataclass(frozen=True)
class DailyProfile:
    """Fator de carga por período (ex.: madrugada baixa, noite em pico)."""

    factors: dict[str, float]

    def __post_init__(self):
        if not self.factors:
            raise ValueError("O perfil diário precisa de ao menos um período.")
        if any(factor <= 0 for factor in self.factors.values()):
            raise ValueError("Os fatores do perfil diário devem ser positivos.")


@dataclass(frozen=True)
class LoadLevel:
    name: str
    requests: int
    multiplier: float = 1.0

    def __post_init__(self):
        if not self.name:
            raise ValueError("O nível de carga precisa de um nome.")
        if type(self.requests) is not int or self.requests < 1:
            raise ValueError("requests deve ser um inteiro positivo.")
        if self.multiplier <= 0:
            raise ValueError("multiplier deve ser maior que zero.")


@dataclass(frozen=True)
class ScenarioConfig:
    topologies: tuple[str, ...]
    link_capacity: int
    seed: int
    repetitions: int
    algorithms: tuple[str, ...]
    base_bandwidth: float
    noise: float
    profile: DailyProfile
    load_levels: tuple[LoadLevel, ...]
    parameters: dict[str, dict]

    def __post_init__(self):
        if self.link_capacity <= 0:
            raise ValueError("link_capacity deve ser maior que zero.")
        if self.base_bandwidth <= 0:
            raise ValueError("base_bandwidth deve ser maior que zero.")
        if not 0 <= self.noise < 1:
            raise ValueError("noise deve estar em [0, 1).")
        if not self.load_levels:
            raise ValueError("Informe ao menos um nível de carga.")
        if len({level.name for level in self.load_levels}) != len(self.load_levels):
            raise ValueError("Os nomes dos níveis de carga devem ser únicos.")


def load_config(path: str | Path) -> ScenarioConfig:
    """Lê o JSON de cenário; chaves ausentes ou desconhecidas são erro."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("A configuração deve ser um objeto JSON.")
    required = {
        "topologies", "link_capacity", "seed", "repetitions", "algorithms",
        "base_bandwidth", "noise", "profile", "load_levels",
    }
    allowed = required | {"parameters"}
    missing, unknown = required - set(raw), set(raw) - allowed
    if missing:
        raise ValueError(f"Chaves ausentes na configuração: {sorted(missing)}")
    if unknown:
        raise ValueError(f"Chaves desconhecidas na configuração: {sorted(unknown)}")
    return ScenarioConfig(
        topologies=tuple(raw["topologies"]),
        link_capacity=raw["link_capacity"],
        seed=raw["seed"],
        repetitions=raw["repetitions"],
        algorithms=tuple(raw["algorithms"]),
        base_bandwidth=raw["base_bandwidth"],
        noise=raw["noise"],
        profile=DailyProfile(dict(raw["profile"])),
        load_levels=tuple(LoadLevel(**level) for level in raw["load_levels"]),
        parameters=dict(raw.get("parameters", {})),
    )


def uniform_capacity(graph: NetworkGraph, capacity: int) -> NetworkGraph:
    """Iguala a capacidade de todos os enlaces (mesma em todas as topologias)."""
    if capacity <= 0:
        raise ValueError("capacity deve ser maior que zero.")
    for link in graph.links:
        link.capacity = capacity
    return graph


def generate_requests(
    graph: NetworkGraph,
    level: LoadLevel,
    profile: DailyProfile,
    *,
    base_bandwidth: float,
    noise: float,
    seed: int,
) -> list[SliceRequest]:
    """Gera `level.requests` requisições com pares origem→destino distintos.

    Pares ordenados, nunca com origem igual ao destino. Os nós são ordenados
    por nome antes do sorteio, pois o grafo os guarda em um conjunto. A banda
    de cada período é base * fator do perfil * multiplicador do nível * ruído
    individual em [1 - noise, 1 + noise], arredondada e com mínimo de 1 Mbps.
    """
    names = sorted(node.name for node in graph.nodes)
    pairs = [(a, b) for a in names for b in names if a != b]
    if level.requests > len(pairs):
        raise ValueError(
            f"{level.requests} requisições excedem os {len(pairs)} pares "
            "distintos da topologia."
        )
    rng = random.Random(f"{seed}:{level.name}")
    chosen = rng.sample(pairs, level.requests)
    requests = []
    for index, (source, destination) in enumerate(chosen, start=1):
        demands = []
        for period, factor in profile.factors.items():
            variation = rng.uniform(1 - noise, 1 + noise)
            bandwidth = max(
                1, round(base_bandwidth * factor * level.multiplier * variation)
            )
            demands.append(SliceDemand(period, bandwidth))
        requests.append(SliceRequest(
            f"request-{index}", Node(source), Node(destination), demands
        ))
    return requests
