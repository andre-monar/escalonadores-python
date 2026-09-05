import copy

from models.periodo import Periodo, TipoPeriodo
from models.resultado import ResultadoSimulacao
from models.tarefa import Tarefa

from algoritmos._montar_resultado import montar_resultado

def sjf(tarefas: list[Tarefa], ctx_time: float) -> ResultadoSimulacao:

    periodos_por_tarefa: dict[int, list[Periodo]] = {tarefa.id: [] for tarefa in tarefas}

    tarefas_ordenadas = sorted(tarefas, key=lambda t: (t.chegada, t.id))
    tempo_atual = tarefas_ordenadas[0].chegada
    tarefas_pendentes = copy.deepcopy(tarefas_ordenadas)
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

    while tarefas_pendentes:
        # encher a fila com tarefas que chegaram até o tempo atual e estão fora dela
        fila = _encher_fila(tarefas_pendentes, tempo_atual, fila)
        
        if not fila:
            # se a fila estiver vazia, incrementa o tempo até a próxima tarefa chegar
            if tarefas_pendentes:
                tempo_atual = min(tarefa.chegada for tarefa in tarefas_pendentes)
            continue

        tarefa_atual = fila.pop(0)
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
            fim=tempo_atual + tarefa_atual.tp,
            tipo=TipoPeriodo.EXECUCAO
        ))
        tempo_atual += tarefa_atual.tp

        # remover tarefa da lista de pendentes
        tarefas_pendentes.remove(tarefa_atual)

    return montar_resultado(
        tarefas, periodos_por_tarefa,
        algoritmo="SJF", ctx_time=ctx_time,
    )
