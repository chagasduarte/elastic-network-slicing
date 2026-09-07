from dataclasses import dataclass, field


@dataclass(frozen=True)
class Node:
    name: str
    def __post_init__(self):
        if(self.name == None):
            raise ValueError(
                            "O nó precisa de um nome."
                        )
           
    