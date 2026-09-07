from dataclasses import dataclass


@dataclass(frozen=True)
class SliceDemand:
    id: str
    bandwidth: int

    def __post_init__(self):
        if not self.id:
            raise ValueError(
                "O identificador do período é obrigatório."
            )

        if self.bandwidth <= 0:
            raise ValueError(
                "A largura de banda deve ser maior que zero."
            )