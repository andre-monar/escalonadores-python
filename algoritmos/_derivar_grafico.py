from models.periodo import TipoPeriodo
from models.resultado import TarefaResultado
from models.tarefa import Recurso

BLOQUEIOS = (TipoPeriodo.BLOQUEIO_DIRETO, TipoPeriodo.BLOQUEIO_INVERSAO)


def calcular_esperas(tr: TarefaResultado) -> list[tuple[float, float]]:
    """Espera nunca é um Periodo de verdade (nenhum algoritmo registra) — é
    derivada aqui: os buracos entre a chegada e o que os períodos já cobrem.
    Não conta o tempo depois do último período (aí a tarefa já terminou)."""
    periodos_ordenados = sorted(tr.periodos, key=lambda p: p.inicio)
    esperas = []
    posicao = tr.tarefa.chegada
    for periodo in periodos_ordenados:
        if periodo.inicio > posicao:
            esperas.append((posicao, periodo.inicio))
        posicao = max(posicao, periodo.fim)
    return esperas


def _tempo_absoluto_em(periodos_execucao, alvo_tempo_proprio):
    """Acha o instante absoluto em que a tarefa alcança `alvo_tempo_proprio`
    de execução própria — caminhando pelos períodos de EXECUCAO em ordem (é
    só neles que o tempo próprio avança). None se ela nunca chega lá."""
    executado = 0
    for periodo in periodos_execucao:
        duracao_periodo = periodo.fim - periodo.inicio
        if executado + duracao_periodo >= alvo_tempo_proprio:
            return periodo.inicio + (alvo_tempo_proprio - executado)
        executado += duracao_periodo
    return None


def _subtrair_bloqueios(recurso: Recurso, inicio: float, fim: float, bloqueios) -> list[tuple[Recurso, float, float]]:
    """Quebra [inicio, fim) pulando qualquer trecho coberto por um bloqueio
    da própria tarefa — bloqueada significa exatamente que ela ainda não tem
    o recurso (R5), só depois que o bloqueio termina ela volta a ser dona."""
    segmentos = []
    posicao = inicio
    for bloqueio in bloqueios:
        if bloqueio.fim <= posicao or bloqueio.inicio >= fim:
            continue  # bloqueio fora do intervalo, não afeta esse recurso
        if bloqueio.inicio > posicao:
            segmentos.append((recurso, posicao, bloqueio.inicio))
        posicao = max(posicao, bloqueio.fim)
    if posicao < fim:
        segmentos.append((recurso, posicao, fim))
    return segmentos


def calcular_recursos_em_uso(tr: TarefaResultado) -> list[tuple[Recurso, float, float]]:
    """Pra cada Recurso da tarefa (janela medida no tempo de execução própria
    dela, C7), acha o instante absoluto em que ela alcança o início e o fim
    da seção crítica. Entre os dois, ela é dona do recurso o tempo todo —
    inclusive em trechos que não são EXECUCAO (pendente, por exemplo) —
    EXCETO onde ela mesma estiver bloqueada: bloqueio é justamente ela ainda
    não ter conseguido o recurso, então esses trechos saem do resultado."""
    periodos_execucao = sorted(
        (p for p in tr.periodos if p.tipo == TipoPeriodo.EXECUCAO),
        key=lambda p: p.inicio,
    )
    bloqueios = sorted(
        (p for p in tr.periodos if p.tipo in BLOQUEIOS),
        key=lambda p: p.inicio,
    )

    segmentos = []
    for recurso in tr.tarefa.recursos:
        abs_inicio = _tempo_absoluto_em(periodos_execucao, recurso.inicio)
        abs_fim = _tempo_absoluto_em(periodos_execucao, recurso.inicio + recurso.duracao)
        if abs_inicio is None or abs_fim is None:
            continue
        segmentos.extend(_subtrair_bloqueios(recurso, abs_inicio, abs_fim, bloqueios))
    return segmentos
