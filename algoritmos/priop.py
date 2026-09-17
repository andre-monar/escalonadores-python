import copy

from models.periodo import Periodo, TipoPeriodo
from models.resultado import ResultadoSimulacao
from models.tarefa import Tarefa

from algoritmos._montar_resultado import montar_resultado


def priop(tarefas: list[Tarefa], ctx_time: float, protocolo: str | None = None) -> ResultadoSimulacao:
    periodos_por_tarefa: dict[int, list[Periodo]] = {tarefa.id: [] for tarefa in tarefas}
    bloqueio_aberto_por_tarefa: dict[int, float] = {}

    tarefas_ordenadas = sorted(tarefas, key=lambda t: (t.chegada, t.id))
    tempo_atual = tarefas_ordenadas[0].chegada
    tarefas_pendentes = copy.deepcopy(tarefas_ordenadas)
    ids_nao_finalizados = {tarefa.id for tarefa in tarefas_ordenadas}
    tp_original_por_id = {tarefa.id: tarefa.tp for tarefa in tarefas_ordenadas}
    prioridade_original_por_id = {tarefa.id: tarefa.prioridade for tarefa in tarefas_ordenadas}
    teto_por_recurso: dict[int, int] = {}
    for tarefa in tarefas_ordenadas:
        for recurso in tarefa.recursos:
            teto_por_recurso[recurso.id] = max(
                teto_por_recurso.get(recurso.id, tarefa.prioridade), tarefa.prioridade,
            )
    fila: list[Tarefa]= []
    tarefa_atual = None

    def _encher_fila(tarefas_pendentes, tempo_atual, fila):
        for tarefa_iterada in tarefas_pendentes:
            if tempo_atual >= tarefa_iterada.chegada and tarefa_iterada not in fila:
                if not fila:
                    fila.append(tarefa_iterada)
                    continue
                # se a fila não estiver vazia, adiciona a tarefa na posição correta
                for i, tarefa_na_fila in enumerate(fila):
                    if tarefa_iterada.prioridade > tarefa_na_fila.prioridade:
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

    def _recurso_esta_sendo_usado(tarefa, recurso_id):
        tempo_executado = tp_original_por_id[tarefa.id] - tarefa.tp
        for recurso in tarefa.recursos:
            if recurso.id == recurso_id and recurso.inicio < tempo_executado < recurso.inicio + recurso.duracao:
                return True
        return False

    def _busca_recursos_solicitados_pela_tarefa(tarefa):
        tempo_executado = tp_original_por_id[tarefa.id] - tarefa.tp
        return [recurso for recurso in tarefa.recursos if recurso.inicio == tempo_executado]

    def _tp_ate_soltar_recurso(tarefa):
        tempo_executado = tp_original_por_id[tarefa.id] - tarefa.tp
        for recurso in tarefa.recursos:
            if recurso.inicio <= tempo_executado < recurso.inicio + recurso.duracao:
                return recurso.inicio + recurso.duracao - tempo_executado
        return None

    def _reverter_prioridade_se_soltou(tarefa):
        tempo_executado = tp_original_por_id[tarefa.id] - tarefa.tp
        for recurso in tarefa.recursos:
            if tempo_executado == recurso.inicio + recurso.duracao:
                tarefa.prioridade = prioridade_original_por_id[tarefa.id]
                return

    def _tp_ate_pedir_recurso(tarefa):
        tempo_executado = tp_original_por_id[tarefa.id] - tarefa.tp
        inicios_futuros = [
            recurso.inicio - tempo_executado
            for recurso in tarefa.recursos
            if recurso.inicio > tempo_executado
        ]
        return min(inicios_futuros) if inicios_futuros else None

    def _bloquear_tarefa(tarefa, tempo_atual):
        """Marca o início de um bloqueio, só se ela não já tiver um em
        aberto — chamadas repetidas enquanto ela continua bloqueada não
        reabrem um novo período, só a primeira vez conta o início."""
        if tarefa.id in bloqueio_aberto_por_tarefa:
            return
        bloqueio_aberto_por_tarefa[tarefa.id] = tempo_atual

    def _desbloquear_tarefa_se_bloqueada(tarefa, tempo_atual):
        """Fecha o bloqueio em aberto dessa tarefa (se tiver algum),
        registrando o período completo agora que sabemos o fim."""
        inicio_bloqueio = bloqueio_aberto_por_tarefa.pop(tarefa.id, None)
        if inicio_bloqueio is None:
            return
        periodos_por_tarefa[tarefa.id].append(Periodo(
            inicio=inicio_bloqueio,
            fim=tempo_atual,
            tipo=TipoPeriodo.BLOQUEIO_DIRETO,
        ))

    def _proxima_tarefa_valida(fila, tarefas_pendentes, tempo_atual):
        for candidata in fila:
            recursos_solicitados = _busca_recursos_solicitados_pela_tarefa(candidata)
            bloqueada = False
            for recurso in recursos_solicitados:
                detentora = next(
                    (outra for outra in tarefas_pendentes
                     if outra is not candidata and _recurso_esta_sendo_usado(outra, recurso.id)),
                    None,
                )
                if detentora is not None:
                    if protocolo == "Herança" and candidata.prioridade > detentora.prioridade:
                        detentora.prioridade = candidata.prioridade
                    _bloquear_tarefa(candidata, tempo_atual)
                    bloqueada = True
                    break
            if not bloqueada:
                _desbloquear_tarefa_se_bloqueada(candidata, tempo_atual)
                if protocolo == "Teto":
                    for recurso in recursos_solicitados:
                        candidata.prioridade = max(candidata.prioridade, teto_por_recurso[recurso.id])
                return candidata
        return None

    def _proxima_preempcao(tempo_atual, tarefa_atual, proxima_tarefa):
            final_previsto = tempo_atual + tarefa_atual.tp
            tempo_incremental = tarefa_atual.tp
            if proxima_tarefa is not None and final_previsto > proxima_tarefa.chegada:
                tempo_incremental = proxima_tarefa.chegada - tempo_atual

            # soltar um recurso também é evento!
            tp_ate_soltar = _tp_ate_soltar_recurso(tarefa_atual)
            if tp_ate_soltar is not None:
                tempo_incremental = min(tempo_incremental, tp_ate_soltar)

            tp_ate_pedir = _tp_ate_pedir_recurso(tarefa_atual)
            if tp_ate_pedir is not None:
                tempo_incremental = min(tempo_incremental, tp_ate_pedir)

            return tempo_incremental

    while ids_nao_finalizados:
        # definir tarefa
        fila = _encher_fila(tarefas_pendentes, tempo_atual, fila)
        if not fila:
            # se a fila estiver vazia, incrementa o tempo até a próxima tarefa chegar
            if tarefas_pendentes:
                tempo_atual = min(tarefa.chegada for tarefa in tarefas_pendentes)
            continue
        
        # escolhe a primeira da fila válida
        # ou seja, que não será bloqueada por recurso
        candidata = _proxima_tarefa_valida(fila, tarefas_pendentes, tempo_atual)
        if candidata is None:
            continue 
        
        # verificar se tarefa mudou, pra inserir ctx
        trocou = False
        if tarefa_atual is None or tarefa_atual != candidata:
            trocou = True

        fila.remove(candidata)
        tarefa_atual = candidata
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

        _reverter_prioridade_se_soltou(tarefa_atual)

        # remover tarefa se ela tiver terminado
        if tarefa_atual.tp <= 0:
            ids_nao_finalizados.remove(tarefa_atual.id)
            tarefas_pendentes.remove(tarefa_atual)

    return montar_resultado(
        tarefas, periodos_por_tarefa,
        algoritmo="PRIOp", ctx_time=ctx_time, protocolo=protocolo,
    )
