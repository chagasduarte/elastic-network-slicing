import math
from dataclasses import dataclass


@dataclass(frozen=True)
class QLearningConfig:
    episodes: int = 2000
    learning_rate: float = 0.2
    discount_factor: float = 1.0
    epsilon_start: float = 1.0
    epsilon_min: float = 0.05
    epsilon_decay: float = 0.995
    max_steps_per_episode: int | None = None
    path_change_penalty: float = 0.15

    def __post_init__(self):
        for name in ("episodes", "max_steps_per_episode"):
            value = getattr(self, name)
            if name == "max_steps_per_episode" and value is None:
                continue
            if type(value) is not int or value <= 0:
                raise ValueError(f"{name} deve ser um inteiro maior que zero.")

        for name in (
            "learning_rate", "discount_factor", "epsilon_start",
            "epsilon_min", "epsilon_decay", "path_change_penalty",
        ):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
            ):
                raise ValueError(f"{name} deve ser um número finito.")

        if not 0 < self.learning_rate <= 1:
            raise ValueError("learning_rate deve estar em (0, 1].")
        if not 0 <= self.discount_factor <= 1:
            raise ValueError("discount_factor deve estar em [0, 1].")
        if not 0 <= self.epsilon_min <= self.epsilon_start <= 1:
            raise ValueError("Use 0 <= epsilon_min <= epsilon_start <= 1.")
        if not 0 < self.epsilon_decay <= 1:
            raise ValueError("epsilon_decay deve estar em (0, 1].")
        if self.path_change_penalty < 0:
            raise ValueError("path_change_penalty não pode ser negativa.")
