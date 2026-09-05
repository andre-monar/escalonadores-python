from models.periodo import Periodo, TipoPeriodo
from models.resultado import ResultadoSimulacao
from models.tarefa import Tarefa

from algoritmos._montar_resultado import montar_resultado

def fcfs(tarefas: list[Tarefa], ctx_time: float) -> ResultadoSimulacao:
    periodos_por_tarefa: dict[int, list[Periodo]] = {tarefa.id: [] for tarefa in tarefas}
    tarefas_ordenadas = sorted(tarefas, key=lambda t: (t.chegada, t.id))
    tempo_atual = tarefas_ordenadas[0].chegada
    for tarefa in tarefas_ordenadas:
        tempo_atual = max(tempo_atual, tarefa.chegada)
        # add troca de contexto
        periodos_por_tarefa[tarefa.id].append(Periodo(
            inicio=tempo_atual,
            fim=tempo_atual + ctx_time,
            tipo=TipoPeriodo.TROCA_CONTEXTO
        ))
        tempo_atual += ctx_time

        # add execucao
        periodos_por_tarefa[tarefa.id].append(Periodo(
            inicio=tempo_atual,
            fim=tempo_atual + tarefa.tp,
            tipo=TipoPeriodo.EXECUCAO
        ))
        tempo_atual += tarefa.tp

        
    return montar_resultado(
        tarefas, periodos_por_tarefa,
        algoritmo="FCFS", ctx_time=ctx_time,
    )
