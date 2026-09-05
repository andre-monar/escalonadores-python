import unittest

from algoritmos.srtf import srtf
from models.tarefa import Tarefa

# Cenário da Aula 5 (enunciado) — mesmas 5 tarefas do FCFS/SJF/RR.
TAREFAS = [
    Tarefa(id=1, chegada=0, tp=5, prioridade=2),
    Tarefa(id=2, chegada=0, tp=2, prioridade=3),
    Tarefa(id=3, chegada=1, tp=4, prioridade=1),
    Tarefa(id=4, chegada=3, tp=1, prioridade=4),
    Tarefa(id=5, chegada=5, tp=2, prioridade=5),
]


class TestSRTF(unittest.TestCase):
    def test_sem_custo_de_troca(self):
        # ordem esperada: T2(0-2) T3(2-3, interrompida por T4) T4(3-4)
        # T3 retoma(4-7, empate com T5 em t=5, T3 continua por ter id menor) T5(7-9) T1(9-14)
        resultado = srtf(TAREFAS, ctx_time=0)
        self.assertAlmostEqual(resultado.medias.tt, 5.4, delta=0.05)
        self.assertAlmostEqual(resultado.medias.tw, 2.6, delta=0.05)

    def test_com_custo_de_troca(self):
        # com ctx_time=1 nenhuma chegada cai no meio de uma execução nesse
        # cenário específico (a folga do ctx empurra tudo pra coincidir com
        # o fim natural de cada tarefa) — por isso dá igual ao SJF aqui, não
        # é engano, é só uma coincidência dos números desse cenário
        resultado = srtf(TAREFAS, ctx_time=1)
        self.assertAlmostEqual(resultado.medias.tt, 7.8, delta=0.05)
        self.assertAlmostEqual(resultado.medias.tw, 5.0, delta=0.05)

    def test_eficiencia_nao_definida(self):
        # SRTF não tem quantum, então a eficiência (R4) não é definida.
        resultado = srtf(TAREFAS, ctx_time=1)
        self.assertIsNone(resultado.parametros.eficiencia)


if __name__ == "__main__":
    unittest.main()
