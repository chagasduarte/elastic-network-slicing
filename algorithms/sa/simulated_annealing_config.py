# algorithms/simulated_annealing/simulated_annealing_config.py

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class SimulatedAnnealingConfig:
    initial_temperature: float = 0.25
    minimum_temperature: float = 0.001
    cooling_rate: float = 0.95

    max_iterations: int = 500

    neighbor_attempts: int = 30
    max_neighbor_steps: int = 20

    hop_weight: float = 0.20
    avg_utilization_weight: float = 0.30
    bottleneck_weight: float = 0.35
    path_change_weight: float = 0.15

    def __post_init__(self):
        if self.initial_temperature <= 0:
            raise ValueError(
                "initial_temperature must be greater than zero"
            )

        if self.minimum_temperature <= 0:
            raise ValueError(
                "minimum_temperature must be greater than zero"
            )

        if not 0 < self.cooling_rate < 1:
            raise ValueError(
                "cooling_rate must be between 0 and 1"
            )

        if self.max_iterations <= 0:
            raise ValueError(
                "max_iterations must be greater than zero"
            )

        total_weight = (
            self.hop_weight
            + self.avg_utilization_weight
            + self.bottleneck_weight
            + self.path_change_weight
        )

        if not math.isclose(total_weight, 1.0):
            raise ValueError(
                "The cost weights must sum to 1.0"
            )