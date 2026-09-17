from dataclasses import dataclass
from enum import Enum


class TipoPeriodo(str, Enum):
    EXECUCAO = "execucao"
    TROCA_CONTEXTO = "troca_contexto"
    BLOQUEIO_DIRETO = "bloqueio_direto"
    BLOQUEIO_INVERSAO = "bloqueio_inversao"


@dataclass
class Periodo:
    inicio: float
    fim: float
    tipo: TipoPeriodo
