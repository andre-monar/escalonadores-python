import copy

from models.periodo import Periodo, TipoPeriodo
from models.resultado import ResultadoSimulacao
from models.tarefa import Tarefa

from algoritmos._montar_resultado import montar_resultado
from algoritmos.validacoes import validar_quantum

def round_robin(tarefas: list[Tarefa], ctx_time: float, quantum: int) -> ResultadoSimulacao:
    validar_quantum(ctx_time, quantum)

    periodos_por_tarefa: dict[int, list[Periodo]] = {tarefa.id: [] for tarefa in tarefas}
    
    fila: list[Tarefa] = []
    tarefas_ordenadas = sorted(tarefas, key=lambda t: (t.chegada, t.id))
    tempo_atual = tarefas_ordenadas[0].chegada
    ids_nao_finalizados = {tarefa.id for tarefa in tarefas_ordenadas}
    tarefas_pendentes = copy.deepcopy(tarefas_ordenadas)
    tarefa_atual = None

    def _encher_fila_e_remover_da_lista(tarefas_pendentes, tempo_atual, fila):
            remover_da_lista = []
            for tarefa in tarefas_pendentes:
                if tempo_atual >= tarefa.chegada and tarefa not in fila:
                    fila.append(tarefa)
                    remover_da_lista.append(tarefa)
            
            for tarefa in remover_da_lista:
                tarefas_pendentes.remove(tarefa)

            return fila, tarefas_pendentes

    while ids_nao_finalizados:
        # encher a fila com tarefas que chegaram até o tempo atual e estão fora dela
        fila, tarefas_pendentes = _encher_fila_e_remover_da_lista(tarefas_pendentes, tempo_atual, fila)

        if tarefa_atual is not None and tarefa_atual.tp > 0:
            # se a tarefa atual ainda tem tempo restante, ela volta pro fim da fila
            fila.append(tarefa_atual)

        if not fila:
            # se a fila estiver vazia, incrementa o tempo até a próxima tarefa chegar
            if tarefas_pendentes:
                tempo_atual = min(tarefa.chegada for tarefa in tarefas_pendentes)
            continue
        tarefa_nova = fila.pop(0)
        
        quantum_pendente = quantum
        # add troca de contexto se tarefa mudou
        if tarefa_atual is None or tarefa_nova.id != tarefa_atual.id:
            tarefa_atual = tarefa_nova
            # add troca de contexto
            periodos_por_tarefa[tarefa_atual.id].append(Periodo(
                inicio=tempo_atual,
                fim=tempo_atual + ctx_time,
                tipo=TipoPeriodo.TROCA_CONTEXTO
            ))
            tempo_atual += ctx_time
            quantum_pendente -= ctx_time

        # add execucao
        periodos_por_tarefa[tarefa_atual.id].append(Periodo(
            inicio=tempo_atual,
            fim=tempo_atual + min(quantum_pendente, tarefa_atual.tp),
            tipo=TipoPeriodo.EXECUCAO,
            preemptado_por_quantum=quantum_pendente < tarefa_atual.tp,
        ))

        # incrementa o tempo
        # em quantum -> se quantum for maior que o tempo da tarefa
        # em tempo tarefa -> o quantum reseta para a proxima, ja que a terefa
        # acabou no meio da janela!
        # quantum pendente pq se tiver troca de contexto, o tempo atual ja foi incrementado com o ctx_time, e o quantum pendente é o que sobrou pra execução da tarefa
        tempo_atual += min(quantum_pendente, tarefa_atual.tp)

        # descontar tempo de execução da tarefa
        tarefa_atual.tp -= min(quantum_pendente, tarefa_atual.tp)

        # marca como processado pra checar o while
        if tarefa_atual.tp <= 0:
            ids_nao_finalizados.remove(tarefa_atual.id)

    return montar_resultado(
        tarefas, periodos_por_tarefa,
        algoritmo="RR", ctx_time=ctx_time, quantum=quantum,
        eficiencia=quantum / (quantum + ctx_time),
    )
