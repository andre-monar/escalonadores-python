from dataclasses import dataclass


@dataclass
class SecaoCritica:
    """Trecho da execução própria da tarefa em que ela detém o recurso R (R5-R7)."""
    inicio: int
    duracao: int


@dataclass
class Tarefa:
    id: int
    chegada: int
    tp: int
    prioridade: int
    secao_critica: SecaoCritica | None = None
