import copy

from models.periodo import Periodo, TipoPeriodo
from models.resultado import ResultadoSimulacao
from models.tarefa import Tarefa

from algoritmos._montar_resultado import montar_resultado


def srtf(tarefas: list[Tarefa], ctx_time: float) -> ResultadoSimulacao:
    periodos_por_tarefa: dict[int, list[Periodo]] = {tarefa.id: [] for tarefa in tarefas}

    tarefas_ordenadas = sorted(tarefas, key=lambda t: (t.chegada, t.id))
    tempo_atual = tarefas_ordenadas[0].chegada
    tarefas_pendentes = copy.deepcopy(tarefas_ordenadas)
    ids_nao_finalizados = {tarefa.id for tarefa in tarefas_ordenadas}
    fila: list[Tarefa]= []

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
                        inserir_na_fila.append((i, tarefa_iterada))
                    else:
                        # se for a ultima, adiciona no final
                        if i == len(fila) - 1:
                            inserir_na_fila.append((len(fila), tarefa_iterada))
        if inserir_na_fila:
            for tarefa in inserir_na_fila:
                fila.insert(*tarefa)
        return fila

    while ids_nao_finalizados:
        # definir tarefa
        fila = _encher_fila(tarefas_pendentes, tempo_atual, fila)
        if not fila:
            # se a fila estiver vazia, incrementa o tempo até a próxima tarefa chegar
            if tarefas_pendentes:
                tempo_atual = min(tarefa.chegada for tarefa in tarefas_pendentes)
            continue
        
        tarefa_atual = fila.pop(0)
        # ir só até a próxima tarefa
        # pegar próxima tarefa
        proxima_tarefa = None
        for tarefa in tarefas_ordenadas:
            if tarefa.chegada > tempo_atual:
                if proxima_tarefa is None or tarefa.chegada < proxima_tarefa.chegada:
                    proxima_tarefa = tarefa

        
        final_previsto = tempo_atual + tarefa_atual.tp + ctx_time
        tempo_incremental = tarefa_atual.tp
        
        if proxima_tarefa is not None and final_previsto > proxima_tarefa.chegada:
            tempo_incremental = proxima_tarefa.chegada - tarefa_atual.chegada

        # add troca de contexto
        periodos_por_tarefa[tarefa_atual.id].append(Periodo(
            inicio=tempo_atual,
            fim=tempo_atual + ctx_time,
            tipo=TipoPeriodo.TROCA_CONTEXTO
        ))
        tempo_atual += ctx_time

        # add execucao
        periodos_por_tarefa[tarefa_atual.id].append(Periodo(
            inicio=tempo_atual,
            fim=tempo_atual + tempo_incremental,
            tipo=TipoPeriodo.EXECUCAO
        ))
        tempo_atual += tempo_incremental
        # deduzir tempo da tarefa
        tarefa_atual.tp -= tempo_incremental
        if tarefa_atual.tp <= 0:
            ids_nao_finalizados.remove(tarefa_atual.id)
            tarefas_pendentes.remove(tarefa_atual)

    return montar_resultado(
        tarefas, periodos_por_tarefa,
        algoritmo="SRTF", ctx_time=ctx_time,
    )
