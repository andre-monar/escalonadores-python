from models.periodo import TipoPeriodo
from models.resultado import ResultadoSimulacao

SIMBOLOS = {
    TipoPeriodo.EXECUCAO: "#",
    TipoPeriodo.TROCA_CONTEXTO: "x",
    TipoPeriodo.BLOQUEIO_DIRETO: "b",
    TipoPeriodo.BLOQUEIO_INVERSAO: "B",
}


def imprimir_resultado(resultado: ResultadoSimulacao) -> None:
    """Imprime um ResultadoSimulacao de forma legível no console: linha do tempo
    tipo Gantt em ASCII, tabela de métricas por tarefa e as médias."""
    p = resultado.parametros
    print(f"\n=== {p.algoritmo} ===")
    print(f"ctx_time={p.ctx_time}  quantum={p.quantum}  protocolo={p.protocolo}  alpha={p.alpha}")

    tempo_max = 0
    for tr in resultado.tarefas.values():
        for periodo in tr.periodos:
            tempo_max = max(tempo_max, int(periodo.fim))

    print("\nLegenda: '#' execução  'x' troca de contexto  'b' bloqueio direto  "
          "'B' bloqueio por inversão  '.' esperando  ' ' ainda não chegou")

    print("\n     " + "".join(str(t % 10) for t in range(tempo_max)))
    for tid in sorted(resultado.tarefas):
        tr = resultado.tarefas[tid]
        linha = ["." if t >= tr.tarefa.chegada else " " for t in range(tempo_max)]
        for periodo in tr.periodos:
            simbolo = SIMBOLOS.get(periodo.tipo, "?")
            for t in range(int(periodo.inicio), int(periodo.fim)):
                if 0 <= t < tempo_max:
                    linha[t] = simbolo
        print(f"T{tid:<3} " + "".join(linha))

    print("\nMétricas por tarefa:")
    print(f"{'ID':<4}{'chegada':<9}{'tp':<5}{'tt':<7}{'tw':<7}{'1a_exec':<9}")
    for tid in sorted(resultado.metricas_por_tarefa):
        m = resultado.metricas_por_tarefa[tid]
        tarefa = resultado.tarefas[tid].tarefa
        print(f"{tid:<4}{tarefa.chegada:<9}{tarefa.tp:<5}{m.tt:<7.1f}{m.tw:<7.1f}{m.t1a_exec:<9.1f}")

    medias = resultado.medias
    print(f"\nMédias -> Tt={medias.tt:.2f}  Tw={medias.tw:.2f}  1a_exec={medias.t1a_exec:.2f}")
    print(f"Eficiência: {p.eficiencia:.3f}" if p.eficiencia is not None else "Eficiência: não definida")
