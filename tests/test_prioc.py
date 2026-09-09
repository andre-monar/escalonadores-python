import unittest

from algoritmos.prioc import prioc
from models.tarefa import Tarefa

# Cenário da Aula 5 (enunciado) — mesmas 5 tarefas do FCFS/SJF/SRTF/RR.
# Convenção: MAIOR valor de prioridade = mais prioritária.
TAREFAS = [
    Tarefa(id=1, chegada=0, tp=5, prioridade=2),
    Tarefa(id=2, chegada=0, tp=2, prioridade=3),
    Tarefa(id=3, chegada=1, tp=4, prioridade=1),
    Tarefa(id=4, chegada=3, tp=1, prioridade=4),
    Tarefa(id=5, chegada=5, tp=2, prioridade=5),
]


class TestPRIOc(unittest.TestCase):
    def test_sem_custo_de_troca(self):
        # ordem esperada: T2(0-2) T1(2-7) T5(7-9) T4(9-10) T3(10-14)
        # (T3 tem a prioridade mais baixa e só roda por último)
        resultado = prioc(TAREFAS, ctx_time=0)
        self.assertAlmostEqual(resultado.medias.tt, 6.6, delta=0.05)
        self.assertAlmostEqual(resultado.medias.tw, 3.8, delta=0.05)

    def test_com_custo_de_troca(self):
        resultado = prioc(TAREFAS, ctx_time=1)
        self.assertAlmostEqual(resultado.medias.tt, 8.0, delta=0.05)
        self.assertAlmostEqual(resultado.medias.tw, 5.2, delta=0.05)

    def test_eficiencia_nao_definida(self):
        # PRIOc não tem quantum, então a eficiência (R4) não é definida.
        resultado = prioc(TAREFAS, ctx_time=1)
        self.assertIsNone(resultado.parametros.eficiencia)


if __name__ == "__main__":
    unittest.main()
