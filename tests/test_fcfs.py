import unittest

from algoritmos.fcfs import fcfs
from models.tarefa import Tarefa

# Cenário da Aula 5 (enunciado, seção 4.1/4.2) — gabarito conhecido.
TAREFAS = [
    Tarefa(id=1, chegada=0, tp=5, prioridade=2),
    Tarefa(id=2, chegada=0, tp=2, prioridade=3),
    Tarefa(id=3, chegada=1, tp=4, prioridade=1),
    Tarefa(id=4, chegada=3, tp=1, prioridade=4),
    Tarefa(id=5, chegada=5, tp=2, prioridade=5),
]


class TestFCFS(unittest.TestCase):
    def test_sem_custo_de_troca(self):
        resultado = fcfs(TAREFAS, ctx_time=0)
        self.assertAlmostEqual(resultado.medias.tt, 8.0, delta=0.05)
        self.assertAlmostEqual(resultado.medias.tw, 5.2, delta=0.05)

    def test_com_custo_de_troca(self):
        resultado = fcfs(TAREFAS, ctx_time=1)
        self.assertAlmostEqual(resultado.medias.tt, 11.0, delta=0.05)
        self.assertAlmostEqual(resultado.medias.tw, 8.2, delta=0.05)

    def test_eficiencia_nao_definida(self):
        # FCFS não tem quantum, então a eficiência (R4) não é definida.
        resultado = fcfs(TAREFAS, ctx_time=1)
        self.assertIsNone(resultado.parametros.eficiencia)


if __name__ == "__main__":
    unittest.main()
