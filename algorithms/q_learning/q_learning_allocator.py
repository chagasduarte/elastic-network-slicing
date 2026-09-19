import math
import random

from algorithms.q_learning.q_learning_config import QLearningConfig
from contracts.slice_allocator import SliceAllocator
from domain.network_graph import NetworkGraph
from domain.slice_demand import SliceDemand
from domain.slice_request import SliceRequest
from domain.slice_result import SliceResult


class QLearningAllocator(SliceAllocator):
    """Aprende rotas por demanda, sem modificar as reservas do grafo.

    O estado é o nó atual e a ação é o próximo nó. Destino, banda,
    capacidades disponíveis e enlaces anteriores ficam fixos durante
    allocate; por isso, a tabela Q é reiniciada a cada chamada.
    """

    def __init__(
        self,
        config: QLearningConfig | None = None,
        seed: int | None = None,
    ):
        self._config = config if config is not None else QLearningConfig()
        self._random = random.Random(seed)
        self._q_table: dict[str, dict[str, float]] = {}

    @property
    def q_table(self) -> dict[str, dict[str, float]]:
        """Cópia dos valores aprendidos na última chamada a allocate."""
        return {node: actions.copy() for node, actions in self._q_table.items()}

    def allocate(
        self,
        graph: NetworkGraph,
        request: SliceRequest,
        demand: SliceDemand,
        previous_result: SliceResult | None = None,
    ) -> SliceResult:
        self._q_table = {}
        source = request.source.name
        destination = request.destination.name

        for label, name in (("origem", source), ("destino", destination)):
            if graph.get_node(name) is None:
                raise ValueError(f"Nó de {label} '{name}' não encontrado.")

        if source == destination:
            self._q_table = {source: {}}
            return self._result(request, demand, [source])

        previous_edges = self._previous_edges(request, previous_result)
        costs = self._build_costs(graph, demand, previous_edges)
        reachable = self._reachable_nodes(costs, destination)
        if source not in reachable:
            return self._result(request, demand, None)

        # O destino é absorvente. A ordenação estabiliza os desempates
        # aleatórios independentemente da ordem de iteração de sets.
        self._q_table = {
            node: (
                {neighbor: 0.0 for neighbor in costs[node]}
                if node != destination else {}
            )
            for node in sorted(reachable)
        }
        max_steps = self._config.max_steps_per_episode
        if max_steps is None:
            max_steps = 4 * len(graph.nodes)

        epsilon = self._config.epsilon_start
        best_path: list[str] | None = None
        best_cost = math.inf

        for _ in range(self._config.episodes):
            current = source
            walk = [source]

            for _ in range(max_steps):
                next_node = self._choose_action(current, epsilon)
                reward = -costs[current][next_node]
                future_value = (
                    0.0 if next_node == destination
                    else max(self._q_table[next_node].values())
                )
                old_value = self._q_table[current][next_node]
                self._q_table[current][next_node] = old_value + (
                    self._config.learning_rate
                    * (
                        reward
                        + self._config.discount_factor * future_value
                        - old_value
                    )
                )
                walk.append(next_node)

                if next_node == destination:
                    path = self._remove_cycles(walk)
                    cost = self._path_cost(path, costs)
                    if cost < best_cost:
                        best_path, best_cost = path, cost
                    break

                # Revisitas são permitidas no treino: as ações dependem
                # apenas do nó, preservando o estado Markoviano. Atingir
                # max_steps trunca a coleta, sem zerar o bootstrap.
                current = next_node

            epsilon = max(
                self._config.epsilon_min,
                epsilon * self._config.epsilon_decay,
            )

        greedy_path = self._greedy_path(source, destination, max_steps)
        if greedy_path is not None:
            greedy_cost = self._path_cost(greedy_path, costs)
            if greedy_cost <= best_cost:
                best_path = greedy_path

        # A alternativa à política gulosa vem dos episódios concluídos,
        # sem executar outro algoritmo de roteamento para fornecer a rota.
        return self._result(request, demand, best_path)

    def _build_costs(
        self,
        graph: NetworkGraph,
        demand: SliceDemand,
        previous_edges: set[frozenset[str]],
    ) -> dict[str, dict[str, float]]:
        costs: dict[str, dict[str, float]] = {
            node.name: {} for node in graph.nodes
        }
        seen_edges: set[frozenset[str]] = set()

        for link in graph.links:
            source, target = link.source.name, link.target.name
            edge = frozenset((source, target))
            # SliceResult identifica enlaces pelos extremos. Assim como
            # NetworkGraph.get_link, considera o primeiro enlace do par.
            if edge in seen_edges:
                continue
            seen_edges.add(edge)
            if not link.supports(demand.id, demand.bandwidth):
                continue

            available = link.available_bandwidth_at(demand.id)
            cost = math.exp(demand.bandwidth / available)
            if previous_edges and edge not in previous_edges:
                cost += self._config.path_change_penalty

            costs[source][target] = cost
            costs[target][source] = cost

        return {
            node: dict(sorted(actions.items()))
            for node, actions in sorted(costs.items())
        }

    @staticmethod
    def _previous_edges(
        request: SliceRequest,
        previous_result: SliceResult | None,
    ) -> set[frozenset[str]]:
        if (
            previous_result is None
            or not previous_result.accepted
            or previous_result.request_id != request.id
            or not previous_result.path
            or previous_result.path[0] != request.source.name
            or previous_result.path[-1] != request.destination.name
        ):
            return set()

        return {
            frozenset((source, target))
            for source, target in zip(
                previous_result.path, previous_result.path[1:]
            )
        }

    @staticmethod
    def _reachable_nodes(
        costs: dict[str, dict[str, float]],
        destination: str,
    ) -> set[str]:
        """Verifica viabilidade sem construir ou escolher uma rota."""
        reachable = {destination}
        pending = [destination]
        while pending:
            current = pending.pop()
            for neighbor in costs[current]:
                if neighbor not in reachable:
                    reachable.add(neighbor)
                    pending.append(neighbor)
        return reachable

    def _choose_action(self, node: str, epsilon: float) -> str:
        values = self._q_table[node]
        if self._random.random() < epsilon:
            return self._random.choice(list(values))
        best_value = max(values.values())
        best_actions = [
            action for action, value in values.items() if value == best_value
        ]
        return self._random.choice(best_actions)

    def _greedy_path(
        self,
        source: str,
        destination: str,
        max_steps: int,
    ) -> list[str] | None:
        path = [source]
        visited = {source}
        for _ in range(min(max_steps, len(self._q_table) - 1)):
            values = self._q_table[path[-1]]
            next_node = max(values, key=values.get)
            if next_node in visited:
                return None
            path.append(next_node)
            if next_node == destination:
                return path
            visited.add(next_node)
        return None

    @staticmethod
    def _remove_cycles(walk: list[str]) -> list[str]:
        path: list[str] = []
        positions: dict[str, int] = {}
        for node in walk:
            if node in positions:
                cut = positions[node] + 1
                for removed in path[cut:]:
                    del positions[removed]
                del path[cut:]
            else:
                positions[node] = len(path)
                path.append(node)
        return path

    def _path_cost(
        self,
        path: list[str],
        costs: dict[str, dict[str, float]],
    ) -> float:
        return sum(
            self._config.discount_factor ** index * costs[source][target]
            for index, (source, target) in enumerate(zip(path, path[1:]))
        )

    @staticmethod
    def _result(
        request: SliceRequest,
        demand: SliceDemand,
        path: list[str] | None,
    ) -> SliceResult:
        return SliceResult(
            request_id=request.id,
            demand_id=demand.id,
            accepted=path is not None,
            path=path if path is not None else [],
            bandwidth=demand.bandwidth if path is not None else 0,
        )
