import unittest

from algoritmos.round_robin import round_robin
from models.tarefa import Tarefa

# Cenário da Aula 5 (enunciado, seções 4.1/4.2) — mesmas 5 tarefas do FCFS.
TAREFAS = [
    Tarefa(id=1, chegada=0, tp=5, prioridade=2),
    Tarefa(id=2, chegada=0, tp=2, prioridade=3),
    Tarefa(id=3, chegada=1, tp=4, prioridade=1),
    Tarefa(id=4, chegada=3, tp=1, prioridade=4),
    Tarefa(id=5, chegada=5, tp=2, prioridade=5),
]

class TestRoundRobin(unittest.TestCase):
    def test_sem_custo_de_troca_quantum_2(self):
        resultado = round_robin(TAREFAS, ctx_time=0, quantum=2)
        self.assertAlmostEqual(resultado.medias.tt, 8.4, delta=0.05)
        self.assertAlmostEqual(resultado.medias.tw, 5.6, delta=0.05)

    def test_com_custo_de_troca_quantum_4(self):
        resultado = round_robin(TAREFAS, ctx_time=1, quantum=4)
        self.assertAlmostEqual(resultado.medias.tt, 13.4, delta=0.05)
        self.assertAlmostEqual(resultado.medias.tw, 10.6, delta=0.05)

    def test_eficiencia_definida(self):
        # Round-Robin tem quantum, então a eficiência (R4) É definida: tq/(tq+ttc).
        resultado = round_robin(TAREFAS, ctx_time=1, quantum=4)
        self.assertAlmostEqual(resultado.parametros.eficiencia, 4 / 5, delta=0.001)


if __name__ == "__main__":
    unittest.main()
