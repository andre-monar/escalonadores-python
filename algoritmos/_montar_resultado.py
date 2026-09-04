from models.periodo import TipoPeriodo, Periodo
from models.resultado import Medias, MetricasTarefa, Parametros, ResultadoSimulacao, TarefaResultado
from models.tarefa import Tarefa


def montar_resultado(
    tarefas: list[Tarefa],
    periodos_por_tarefa: dict[int, list[Periodo]],
    algoritmo: str,
    ctx_time: float,
    quantum: int | None = None,
    eficiencia: float | None = None,
    protocolo: str | None = None,
    alpha: float | None = None,
) -> ResultadoSimulacao:
    """Calcula métricas (tt, tw, 1ª execução) e embrulha tudo num ResultadoSimulacao.

    `periodos_por_tarefa` já deve vir completo — inclusive os períodos de
    TROCA_CONTEXTO, montados manualmente por você durante a simulação. Isso é
    igual pra qualquer algoritmo — a única coisa que muda de um pro outro é como
    `periodos_por_tarefa` foi preenchido (a política de escalonamento em si).
    Chame no final da sua função, depois de ter simulado.
    """
    tarefas_resultado: dict[int, TarefaResultado] = {}
    metricas_por_tarefa: dict[int, MetricasTarefa] = {}

    for tarefa in tarefas:
        periodos = periodos_por_tarefa[tarefa.id]

        conclusao = max(periodo.fim for periodo in periodos)
        tt = conclusao - tarefa.chegada
        tw = tt - tarefa.tp

        inicios_execucao = [p.inicio for p in periodos if p.tipo == TipoPeriodo.EXECUCAO]
        t1a_exec = min(inicios_execucao) - tarefa.chegada

        tarefas_resultado[tarefa.id] = TarefaResultado(tarefa=tarefa, periodos=periodos)
        metricas_por_tarefa[tarefa.id] = MetricasTarefa(tt=tt, tw=tw, t1a_exec=t1a_exec)

    n = len(tarefas)
    medias = Medias(
        tt=sum(m.tt for m in metricas_por_tarefa.values()) / n,
        tw=sum(m.tw for m in metricas_por_tarefa.values()) / n,
        t1a_exec=sum(m.t1a_exec for m in metricas_por_tarefa.values()) / n,
    )

    parametros = Parametros(
        algoritmo=algoritmo, ctx_time=ctx_time, quantum=quantum,
        eficiencia=eficiencia, protocolo=protocolo, alpha=alpha,
    )

    return ResultadoSimulacao(
        tarefas=tarefas_resultado,
        metricas_por_tarefa=metricas_por_tarefa,
        medias=medias,
        parametros=parametros,
    )
