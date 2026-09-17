import tkinter as tk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from models.periodo import TipoPeriodo
from models.resultado import ResultadoSimulacao
from views import theme

CHART_EXECUCAO = theme.PURPLE
CHART_TROCA_CONTEXTO = "#f7b955"
CHART_ESPERA = theme.PURPLE_DARK  # mesma borda da execução/troca, só que vazada (sem preenchimento)
CHART_BLOQUEIO = theme.DANGER  # hachurado -- direto e inversão usam a mesma cor, só muda a trama
HACHURA_BLOQUEIO_DIRETO = "///"
HACHURA_BLOQUEIO_INVERSAO = "xxx"

ALTURA_BARRA = 0.55
ALTURA_RECURSO = ALTURA_BARRA / 3  # faixa central sobre a barra, 1/3 da altura dela


class ChartMixin:
    def _build_chart_panel(self, parent):
        panel = tk.Frame(parent, bg=theme.BG)
        panel.pack(side="left", fill="both", expand=True)

        card = tk.Frame(panel, bg=theme.CARD_BG, highlightbackground=theme.BORDER,
                         highlightthickness=1)
        card.pack(fill="both", expand=True, padx=14, pady=14)

        self.fig = Figure(figsize=(6, 5), dpi=100, facecolor=theme.CARD_BG)
        self.ax = self.fig.add_subplot(111)

        self.chart_canvas = FigureCanvasTkAgg(self.fig, master=card)
        self.chart_canvas.get_tk_widget().configure(bg=theme.CARD_BG, highlightthickness=0)
        self.chart_canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

        self._draw_empty_chart()

    def _style_axes(self):
        self.ax.set_facecolor(theme.CARD_BG)
        self.ax.tick_params(colors=theme.TEXT_MUTED, labelsize=9)
        for spine in self.ax.spines.values():
            spine.set_color(theme.BORDER)
        self.ax.xaxis.label.set_color(theme.TEXT_MUTED)
        self.ax.title.set_color(theme.TEXT)

    def _draw_empty_chart(self):
        self.ax.clear()
        self._style_axes()
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.text(
            0.5, 0.5, "Clique em \"Gerar gráfico\" pra simular",
            transform=self.ax.transAxes, ha="center", va="center",
            color=theme.TEXT_MUTED, fontsize=11,
        )
        self.fig.tight_layout()
        self.chart_canvas.draw()

    def _desenhar_faixa_recurso(self, tarefa_id, inicio, fim, cor, pausado=False):
        """Faixa central sobre a barra da tarefa marcando a posse de um
        recurso — sólida enquanto em uso, hachurada quando pausada (esse
        segundo caso ainda não é produzido por nenhum algoritmo, só o
        desenho já fica pronto pra quando existir)."""
        if pausado:
            self.ax.barh(
                tarefa_id, fim - inicio, left=inicio, height=ALTURA_RECURSO,
                fill=False, hatch="////", edgecolor=cor, linewidth=1,
            )
        else:
            self.ax.barh(
                tarefa_id, fim - inicio, left=inicio, height=ALTURA_RECURSO,
                color=cor, edgecolor=cor, linewidth=0,
            )

    def _desenhar_resultado(self, resultado: ResultadoSimulacao, cores_recursos: dict | None = None):
        self.ax.clear()
        self._style_axes()

        tarefas_resultado = sorted(resultado.tarefas.values(), key=lambda tr: tr.tarefa.id)
        tempo_max = max(periodo.fim for tr in tarefas_resultado for periodo in tr.periodos)

        for tr in tarefas_resultado:
            for inicio, fim in tr.esperas:
                self.ax.barh(
                    tr.tarefa.id, fim - inicio, left=inicio,
                    fill=False, edgecolor=CHART_ESPERA, linewidth=1.2, height=ALTURA_BARRA,
                )
            for periodo in tr.periodos:
                if periodo.tipo in (TipoPeriodo.BLOQUEIO_DIRETO, TipoPeriodo.BLOQUEIO_INVERSAO):
                    hachura = (
                        HACHURA_BLOQUEIO_INVERSAO if periodo.tipo == TipoPeriodo.BLOQUEIO_INVERSAO
                        else HACHURA_BLOQUEIO_DIRETO
                    )
                    self.ax.barh(
                        tr.tarefa.id, periodo.fim - periodo.inicio, left=periodo.inicio,
                        fill=False, hatch=hachura, edgecolor=CHART_BLOQUEIO, linewidth=1,
                        height=ALTURA_BARRA,
                    )
                else:
                    cor = CHART_EXECUCAO if periodo.tipo == TipoPeriodo.EXECUCAO else CHART_TROCA_CONTEXTO
                    borda = theme.PURPLE_DARK
                    self.ax.barh(
                        tr.tarefa.id, periodo.fim - periodo.inicio, left=periodo.inicio,
                        color=cor, edgecolor=borda, linewidth=1.2, height=ALTURA_BARRA,
                    )
                if periodo.preemptado_por_quantum:
                    self.ax.plot(
                        [periodo.fim, periodo.fim], [tr.tarefa.id - 0.32, tr.tarefa.id + 0.32],
                        linestyle="--", color=theme.TEXT, linewidth=1.2,
                    )
            for recurso, inicio, fim in tr.recursos_em_uso:
                cor_recurso = (cores_recursos or {}).get(recurso.id, theme.TEXT)
                self._desenhar_faixa_recurso(tr.tarefa.id, inicio, fim, cor_recurso)
            metricas = resultado.metricas_por_tarefa[tr.tarefa.id]
            self.ax.text(
                tempo_max + tempo_max * 0.02, tr.tarefa.id,
                f"tt={metricas.tt:.1f}  tw={metricas.tw:.1f}",
                va="center", color=theme.TEXT_MUTED, fontsize=8,
            )

        n_trocas = sum(
            1 for tr in tarefas_resultado for periodo in tr.periodos
            if periodo.tipo == TipoPeriodo.TROCA_CONTEXTO
        )

        self.ax.set_yticks([tr.tarefa.id for tr in tarefas_resultado])
        self.ax.set_yticklabels([f"T{tr.tarefa.id}" for tr in tarefas_resultado], color=theme.TEXT)
        self.ax.set_xlim(0, tempo_max * 1.3)
        self.ax.set_xlabel("Tempo")
        self.ax.set_title(
            f"{resultado.parametros.algoritmo}   —   "
            f"Tt médio={resultado.medias.tt:.2f}  Tw médio={resultado.medias.tw:.2f}  "
            f"1ª exec. média={resultado.medias.t1a_exec:.2f}  trocas={n_trocas}",
            fontsize=10, color=theme.TEXT,
        )

        self.fig.tight_layout()
        self.chart_canvas.draw()
