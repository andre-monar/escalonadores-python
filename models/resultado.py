from dataclasses import dataclass, field

from models.periodo import Periodo
from models.tarefa import Tarefa


@dataclass
class TarefaResultado:
    tarefa: Tarefa
    periodos: list[Periodo] = field(default_factory=list)


@dataclass
class MetricasTarefa:
    tt: float
    tw: float
    t1a_exec: float


@dataclass
class Medias:
    tt: float
    tw: float
    t1a_exec: float


@dataclass
class Parametros:
    algoritmo: str
    ctx_time: float
    quantum: int | None = None
    eficiencia: float | None = None
    protocolo: str | None = None
    alpha: float | None = None


@dataclass
class ResultadoSimulacao:
    tarefas: dict[int, TarefaResultado]
    metricas_por_tarefa: dict[int, MetricasTarefa]
    medias: Medias
    parametros: Parametros
