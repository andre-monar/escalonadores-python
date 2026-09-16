from dataclasses import dataclass, field


@dataclass
class Recurso:
    id: int
    inicio: int
    duracao: int


@dataclass
class Tarefa:
    id: int
    chegada: int
    tp: int # tempo processamento
    prioridade: int
    recursos: list[Recurso] = field(default_factory=list)
