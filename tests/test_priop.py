import unittest

from algoritmos.priop import priop
from models.tarefa import Recurso, Tarefa

# Cenário da Aula 5 (enunciado) — mesmas 5 tarefas dos outros algoritmos.
# Fase 1: nenhuma tarefa usa recursos, só testa a preempção por prioridade.
# Convenção: MAIOR valor de prioridade = mais prioritária.
TAREFAS = [
    Tarefa(id=1, chegada=0, tp=5, prioridade=2),
    Tarefa(id=2, chegada=0, tp=2, prioridade=3),
    Tarefa(id=3, chegada=1, tp=4, prioridade=1),
    Tarefa(id=4, chegada=3, tp=1, prioridade=4),
    Tarefa(id=5, chegada=5, tp=2, prioridade=5),
]


class TestPRIOp(unittest.TestCase):
    def test_sem_custo_de_troca(self):
        # ordem esperada: T2(0-2) T1(2-3, interrompida por T4) T4(3-4)
        # T1 retoma(4-5, interrompida por T5) T5(5-7) T1 retoma(7-10) T3(10-14)
        resultado = priop(TAREFAS, ctx_time=0)
        self.assertAlmostEqual(resultado.medias.tt, 5.6, delta=0.05)
        self.assertAlmostEqual(resultado.medias.tw, 2.8, delta=0.05)

    def test_com_custo_de_troca(self):
        # com ctx_time=1 nenhuma chegada cai no meio de uma execução nesse
        # cenário específico (igual aconteceu com SRTF vs SJF) — por isso dá
        # igual ao PRIOc aqui, não é engano
        resultado = priop(TAREFAS, ctx_time=1)
        self.assertAlmostEqual(resultado.medias.tt, 8.0, delta=0.05)
        self.assertAlmostEqual(resultado.medias.tw, 5.2, delta=0.05)

    def test_eficiencia_nao_definida(self):
        # PRIOp não tem quantum, então a eficiência (R4) não é definida.
        resultado = priop(TAREFAS, ctx_time=1)
        self.assertIsNone(resultado.parametros.eficiencia)


class TestPRIOpComRecursos(unittest.TestCase):
    def test_inversao_de_prioridades_sem_protocolo(self):
        # Cenário da Aula 6 (enunciado), 4.3 — inversão de prioridades, sem
        # protocolo de correção (R5). Só t1 (menor prioridade) e t4 (maior)
        # disputam o recurso R; t2 e t3 preemptam t1 sem nunca usar R, o que
        # atrasa t4 bem além do tamanho da própria seção crítica dela.
        tarefas = [
            Tarefa(id=1, chegada=0, tp=6, prioridade=1, recursos=[Recurso(id=1, inicio=1, duracao=4)]),
            Tarefa(id=2, chegada=4, tp=4, prioridade=2),
            Tarefa(id=3, chegada=6, tp=3, prioridade=3),
            Tarefa(id=4, chegada=2, tp=3, prioridade=4, recursos=[Recurso(id=1, inicio=1, duracao=1)]),
        ]
        resultado = priop(tarefas, ctx_time=0)

        self.assertAlmostEqual(resultado.medias.tt, 9.75, delta=0.05)
        self.assertAlmostEqual(resultado.medias.tw, 5.75, delta=0.05)

        tw_esperado = {1: 10, 2: 3, 3: 0, 4: 10}
        for tid, tw in tw_esperado.items():
            self.assertAlmostEqual(resultado.metricas_por_tarefa[tid].tw, tw, delta=0.05)

    def test_heranca_de_prioridade(self):
        # Cenário da Aula 6 (enunciado), 4.4 — mesmas quatro tarefas do 4.3,
        # agora com herança habilitada (R6). Em t=3, t4 bloqueia e t1 herda
        # a prioridade 4; t2/t3 não conseguem mais preemptar t1 até ela
        # soltar o recurso em t=6, quando a prioridade original (1) volta.
        # O bloqueio de t4 cai de 10 (sem protocolo) pra 3.
        tarefas = [
            Tarefa(id=1, chegada=0, tp=6, prioridade=1, recursos=[Recurso(id=1, inicio=1, duracao=4)]),
            Tarefa(id=2, chegada=4, tp=4, prioridade=2),
            Tarefa(id=3, chegada=6, tp=3, prioridade=3),
            Tarefa(id=4, chegada=2, tp=3, prioridade=4, recursos=[Recurso(id=1, inicio=1, duracao=1)]),
        ]
        resultado = priop(tarefas, ctx_time=0, protocolo="Herança")

        self.assertAlmostEqual(resultado.medias.tt, 9.50, delta=0.05)
        self.assertAlmostEqual(resultado.medias.tw, 5.50, delta=0.05)

        tw_esperado = {1: 10, 2: 7, 3: 2, 4: 3}
        for tid, tw in tw_esperado.items():
            self.assertAlmostEqual(resultado.metricas_por_tarefa[tid].tw, tw, delta=0.05)

    def test_teto_de_prioridade(self):
        # Cenário da Aula 6 (enunciado), 4.5 — mesmas quatro tarefas do 4.3,
        # agora com teto habilitado (R7). O teto de R vale 4 (maior
        # prioridade entre t1 e t4) — t1 assume esse valor assim que
        # adquire o recurso em t=1, então t4 nunca chega a preemptar (o
        # bloqueio é prevenido, não só encurtado). As médias coincidem com
        # as da herança, mas por um caminho diferente: t1[0,5) t4[5,8)
        # t3[8,11) t2[11,15) t1[15,16).
        tarefas = [
            Tarefa(id=1, chegada=0, tp=6, prioridade=1, recursos=[Recurso(id=1, inicio=1, duracao=4)]),
            Tarefa(id=2, chegada=4, tp=4, prioridade=2),
            Tarefa(id=3, chegada=6, tp=3, prioridade=3),
            Tarefa(id=4, chegada=2, tp=3, prioridade=4, recursos=[Recurso(id=1, inicio=1, duracao=1)]),
        ]
        resultado = priop(tarefas, ctx_time=0, protocolo="Teto")

        self.assertAlmostEqual(resultado.medias.tt, 9.50, delta=0.05)
        self.assertAlmostEqual(resultado.medias.tw, 5.50, delta=0.05)

        tw_esperado = {1: 10, 2: 7, 3: 2, 4: 3}
        for tid, tw in tw_esperado.items():
            self.assertAlmostEqual(resultado.metricas_por_tarefa[tid].tw, tw, delta=0.05)


if __name__ == "__main__":
    unittest.main()
