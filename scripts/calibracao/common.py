"""Utilidades da calibração: cenários, contadores externos e execução.

Os alocadores não preenchem AlgorithmCounters (todos os campos ficam None).
Para não alterar os algoritmos, os contadores são obtidos aqui, envolvendo
métodos das instâncias (sem mudar o comportamento nem consumir números
aleatórios). Execute da raiz do repositório com
`python3.11 -m scripts.calibracao.<modulo>`.
"""

from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.cli import TOPOLOGIES  # noqa: E402
from experiments.runner import AlgorithmSpec, ExperimentRunner  # noqa: E402
from experiments.scenarios import (  # noqa: E402
    DailyProfile, LoadLevel, generate_requests, uniform_capacity,
)
from main import allocator_parameters, create_allocator  # noqa: E402

PROFILE = {"t1": 0.25, "t2": 0.5, "t3": 0.75, "t4": 1.0}
LINK_CAPACITY = 800
BASE_BANDWIDTH = 40
NOISE = 0.3


def wrap(obj, name, counter, key):
    original = getattr(obj, name)

    def wrapper(*args, **kwargs):
        counter[key] += 1
        return original(*args, **kwargs)

    setattr(obj, name, wrapper)


class CountingAllocator:
    """Delega a um alocador e acumula contadores por chamada a allocate.

    construcoes: candidatos de caminho construídos/gerados (formigas, vizinhos
    do SA, episódios do Q-Learning). avaliados: caminhos completos pontuados
    pela função de custo do próprio algoritmo. expansoes: passos locais
    (nós expandidos / ações escolhidas).
    """

    def __init__(self, algorithm, inner):
        self.inner = inner
        self.counts = Counter()
        self.calls = 0
        self.searched = Counter()
        if algorithm == "aco":
            wrap(inner, "_build_ant_path", self.counts, "construcoes")
            wrap(inner, "_calculate_path_cost", self.counts, "avaliados")
            wrap(inner, "_get_feasible_links", self.counts, "expansoes")
        elif algorithm == "sa":
            wrap(inner._neighbor_generator, "generate", self.counts, "construcoes")
            wrap(inner._neighbor_generator, "_find_suffix", self.counts, "expansoes")
            wrap(inner._cost_calculator, "calculate", self.counts, "avaliados")
        elif algorithm == "q-learning":
            wrap(inner, "_choose_action", self.counts, "expansoes")
            wrap(inner, "_path_cost", self.counts, "avaliados")

    def allocate(self, *args, **kwargs):
        before = Counter(self.counts)
        result = self.inner.allocate(*args, **kwargs)
        delta = self.counts - before
        # Só entram as alocações em que a busca realmente rodou (houve
        # caminho viável de partida); rejeições imediatas não contam esforço.
        if delta["expansoes"] > 0:
            self.calls += 1
            self.searched.update(delta)
        return result


def build_requests(topology, requests, multiplier, scenario_seed):
    level = LoadLevel(f"cal{requests}x{multiplier}", requests, multiplier)
    graph = uniform_capacity(TOPOLOGIES[topology](), LINK_CAPACITY)
    return generate_requests(
        graph, level, DailyProfile(PROFILE),
        base_bandwidth=BASE_BANDWIDTH, noise=NOISE, seed=scenario_seed,
    )


def run_one(topology, requests, algorithm, parameters, seed, count=True):
    """Uma execução; devolve (ExperimentMetrics, contadores médios por alocação)."""
    holder = {}

    def factory(run_seed, service):
        inner = create_allocator(algorithm, service, run_seed, parameters=parameters)
        holder["alloc"] = CountingAllocator(algorithm, inner) if count else inner
        return holder["alloc"]

    spec = AlgorithmSpec(
        algorithm, factory, allocator_parameters(algorithm, parameters),
        stochastic=algorithm != "petic",
    )

    def topo():
        return uniform_capacity(TOPOLOGIES[topology](), LINK_CAPACITY)

    run = ExperimentRunner().run(
        topo, requests, [spec], topology=topology, repetitions=1,
        seed=seed, period_order=tuple(PROFILE),
    )[0]
    counters = {}
    if count and holder["alloc"].calls:
        a = holder["alloc"]
        counters = {k: v / a.calls for k, v in a.searched.items()}
        counters["buscas"] = a.calls
    return run, counters
