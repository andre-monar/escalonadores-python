import copy

from models.periodo import Periodo, TipoPeriodo
from models.resultado import ResultadoSimulacao
from models.tarefa import Tarefa

from algoritmos._montar_resultado import montar_resultado

# algoritmo SRTF:
# - Shortest Remaining Time First
# - é uma variação do SJF, mas preemptivo: tarefas podem ser interrompidas se uma nova tarefa chegar com tempo de processamento menor que o restante da tarefa atual
def srtf(tarefas: list[Tarefa], ctx_time: float) -> ResultadoSimulacao:
    periodos_por_tarefa: dict[int, list[Periodo]] = {tarefa.id: [] for tarefa in tarefas}

    tarefas_ordenadas = sorted(tarefas, key=lambda t: (t.chegada, t.id))
    tempo_atual = tarefas_ordenadas[0].chegada
    tarefas_pendentes = copy.deepcopy(tarefas_ordenadas)
    ids_nao_finalizados = {tarefa.id for tarefa in tarefas_ordenadas}
    fila: list[Tarefa]= []
    tarefa_atual = None

    def _encher_fila(tarefas_pendentes, tempo_atual, fila):
        # variavel pra inserir só fora do loop, nao durante a iteração
        inserir_na_fila: list[tuple[int, Tarefa]] = []
        for tarefa_iterada in tarefas_pendentes:
            if tempo_atual >= tarefa_iterada.chegada and tarefa_iterada not in fila:
                if not fila:
                    fila.append(tarefa_iterada)
                    continue
                # se a fila não estiver vazia, adiciona a tarefa na posição correta
                for i, tarefa_na_fila in enumerate(fila):
                    if tarefa_iterada.tp < tarefa_na_fila.tp:
                        fila.insert(i, tarefa_iterada)
                        break
                    else:
                        # se for a ultima, adiciona no final
                        if i == len(fila) - 1:
                            fila.append(tarefa_iterada)
                            break
        return fila

    def _pegar_proxima_tarefa(tarefas_ordenadas, tempo_atual):
            proxima_tarefa = None
            for tarefa in tarefas_ordenadas:
                if tarefa.chegada > tempo_atual:
                    if proxima_tarefa is None or tarefa.chegada < proxima_tarefa.chegada:
                        proxima_tarefa = tarefa
            return proxima_tarefa

    def _proxima_preempcao(tempo_atual, tarefa_atual, proxima_tarefa):
            final_previsto = tempo_atual + tarefa_atual.tp 
            tempo_incremental = tarefa_atual.tp 
            if proxima_tarefa is not None and final_previsto > proxima_tarefa.chegada:
                tempo_incremental = proxima_tarefa.chegada - tempo_atual
            return tempo_incremental

    while ids_nao_finalizados:
        # definir tarefa
        fila = _encher_fila(tarefas_pendentes, tempo_atual, fila)
        if not fila:
            # se a fila estiver vazia, incrementa o tempo até a próxima tarefa chegar
            if tarefas_pendentes:
                tempo_atual = min(tarefa.chegada for tarefa in tarefas_pendentes)
            continue
        
        # verificar se tarefa mudou, pra inserir ctx
        trocou = False
        if tarefa_atual is None or tarefa_atual != fila[0]:
            trocou = True
        
        tarefa_atual = fila.pop(0)
        proxima_tarefa = _pegar_proxima_tarefa(tarefas_ordenadas, tempo_atual)
       
        # add troca de contexto se tarefa trocou
        if trocou:
            periodos_por_tarefa[tarefa_atual.id].append(Periodo(
                inicio=tempo_atual,
                fim=tempo_atual + ctx_time,
                tipo=TipoPeriodo.TROCA_CONTEXTO
            ))
            tempo_atual += ctx_time

         # ir só até a próxima tarefa (preempta toda vez que uma chega, e ai confere)
        tempo_incremental = _proxima_preempcao(tempo_atual, tarefa_atual, proxima_tarefa)
        
        if tempo_incremental > 0:
            # add execucao
            periodos_por_tarefa[tarefa_atual.id].append(Periodo(
                inicio=tempo_atual,
                fim=tempo_atual + tempo_incremental,
                tipo=TipoPeriodo.EXECUCAO
            ))
            tempo_atual += tempo_incremental

        # deduzir tempo da tarefa
        tarefa_atual.tp -= tempo_incremental

        # remover tarefa se ela tiver terminado
        if tarefa_atual.tp <= 0:
            ids_nao_finalizados.remove(tarefa_atual.id)
            tarefas_pendentes.remove(tarefa_atual)

    return montar_resultado(
        tarefas, periodos_por_tarefa,
        algoritmo="SRTF", ctx_time=ctx_time,
    )
