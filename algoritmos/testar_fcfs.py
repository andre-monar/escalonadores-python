"""Roda o fcfs() com dados mockados e imprime o resultado no console pra teste manual.

Uso:
    python -m algoritmos.testar_fcfs
"""
from algoritmos._debug_print import imprimir_resultado
from algoritmos.fcfs import fcfs
from models.tarefa import Tarefa

# Cenário da Aula 5 (enunciado, seção 4.1) — tem gabarito conhecido pra conferir.
TAREFAS_MOCK = [
    Tarefa(id=1, chegada=0, tp=5, prioridade=2),
    Tarefa(id=2, chegada=0, tp=2, prioridade=3),
    Tarefa(id=3, chegada=1, tp=4, prioridade=1),
    Tarefa(id=4, chegada=3, tp=1, prioridade=4),
    Tarefa(id=5, chegada=5, tp=2, prioridade=5),
]

# Médias esperadas: seção 4.1 do enunciado (sem custo de troca) e seção 4.2 (c=1).
GABARITO = {
    0: {"tt": 8.0, "tw": 5.2},
    1: {"tt": 11.0, "tw": 8.2},
}


def main(ctx_time: float = 0) -> None:
    resultado = fcfs(TAREFAS_MOCK, ctx_time=ctx_time)
    imprimir_resultado(resultado)

    gabarito = GABARITO.get(ctx_time)
    if gabarito is None:
        return

    print(f"\nConferência com o gabarito do enunciado (ctx_time={ctx_time}):")
    for chave, esperado in gabarito.items():
        obtido = getattr(resultado.medias, chave)
        ok = abs(obtido - esperado) < 0.05
        print(f"  {chave}: obtido={obtido:.2f}  esperado={esperado}  {'OK' if ok else 'DIVERGE'}")


if __name__ == "__main__":
    main(ctx_time=0)
    main(ctx_time=1)
