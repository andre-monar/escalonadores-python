import tkinter as tk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from models.periodo import TipoPeriodo
from models.resultado import ResultadoSimulacao
from views import theme
from views.components.chart_legend import (
    CHART_BLOQUEIO,
    CHART_ESPERA,
    CHART_EXECUCAO,
    CHART_TROCA_CONTEXTO,
    HACHURA_BLOQUEIO_DIRETO,
    construir_legenda,
)
from views.components.chart_summary_table import construir_tabela_resumo

ALTURA_BARRA = 0.55
ALTURA_RECURSO = ALTURA_BARRA / 3  # faixa central sobre a barra, 1/3 da altura dela

GAP_LEGENDA = 0.015  # respiro entre o eixo X e o topo da legenda
FOLGA_INFERIOR = 0.005  # respiro entre o fundo da legenda e a borda da figura


def _dividir_por_execucao(periodos, inicio, fim):
    """Recorta [inicio, fim) — um intervalo de posse de recurso, já calculado
    por `calcular_recursos_em_uso` — nos trechos em que a tarefa está de fato
    em EXECUCAO e no que sobra (ela já cruzou o próprio limiar do recurso,
    mas está parada: espera, troca de contexto ou bloqueio). Regra simples,
    por tarefa — não confere se outra tarefa também reivindica o mesmo
    recurso nesse meio-tempo."""
    execucoes = sorted(
        (max(p.inicio, inicio), min(p.fim, fim))
        for p in periodos
        if p.tipo == TipoPeriodo.EXECUCAO and p.inicio < fim and p.fim > inicio
    )
    segmentos = []
    posicao = inicio
    for inicio_exec, fim_exec in execucoes:
        if inicio_exec > posicao:
            segmentos.append((posicao, inicio_exec, False))
        segmentos.append((inicio_exec, fim_exec, True))
        posicao = fim_exec
    if posicao < fim:
        segmentos.append((posicao, fim, False))
    return segmentos


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
        if getattr(self, "_tabela_resumo_ax", None) is not None:
            self._tabela_resumo_ax.remove()
            self._tabela_resumo_ax = None

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
        recurso — sólida enquanto a tarefa está de fato em EXECUCAO,
        hachurada (vazada) nos trechos em que ela já cruzou o próprio
        limiar do recurso mas está parada (espera, troca de contexto ou
        bloqueio) — desenhada depois das barras de bloqueio, por isso
        sobrepõe a hachura delas."""
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
        if getattr(self, "_tabela_resumo_ax", None) is not None:
            self._tabela_resumo_ax.remove()
            self._tabela_resumo_ax = None

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
                if periodo.tipo == TipoPeriodo.BLOQUEIO_DIRETO:
                    self.ax.barh(
                        tr.tarefa.id, periodo.fim - periodo.inicio, left=periodo.inicio,
                        fill=False, hatch=HACHURA_BLOQUEIO_DIRETO, edgecolor=CHART_BLOQUEIO, linewidth=1,
                        height=ALTURA_BARRA,
                    )
                else:
                    cor = CHART_EXECUCAO if periodo.tipo == TipoPeriodo.EXECUCAO else CHART_TROCA_CONTEXTO
                    borda = theme.PURPLE_DARK
                    self.ax.barh(
                        tr.tarefa.id, periodo.fim - periodo.inicio, left=periodo.inicio,
                        color=cor, edgecolor=borda, linewidth=1.2, height=ALTURA_BARRA,
                    )
            for instante in tr.preempcoes:
                self.ax.plot(
                    [instante, instante], [tr.tarefa.id - 0.32, tr.tarefa.id + 0.32],
                    linestyle="--", color=theme.TEXT, linewidth=1.2,
                )
            for recurso, inicio, fim in tr.recursos_em_uso:
                cor_recurso = (cores_recursos or {}).get(recurso.id, theme.TEXT)
                for sub_inicio, sub_fim, executando in _dividir_por_execucao(tr.periodos, inicio, fim):
                    self._desenhar_faixa_recurso(
                        tr.tarefa.id, sub_inicio, sub_fim, cor_recurso, pausado=not executando,
                    )
            metricas = resultado.metricas_por_tarefa[tr.tarefa.id]
            self.ax.text(
                tempo_max + tempo_max * 0.02, tr.tarefa.id,
                f"Prioridade={tr.tarefa.prioridade}\ntt={metricas.tt:.1f} s  tw={metricas.tw:.1f} s",
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

        self._ajustar_layout(tarefas_resultado, cores_recursos, resultado, n_trocas)
        self.chart_canvas.draw()

    def _ajustar_layout(self, tarefas_resultado, cores_recursos, resultado, n_trocas):
        """Reserva embaixo só o espaço que o mais alto dos dois — legenda
        (direita) ou tabela de resumo (esquerda) — realmente precisa. O
        tight_layout nunca encolhe o eixo além do que ele mesmo já reserva
        pros próprios rótulos — pedir uma margem via `rect` menor que isso
        não tem efeito nenhum, só sobra espaço vazio. Por isso o
        posicionamento final é direto (`ax.set_position`), calculado a
        partir da altura real de cada um já desenhado (não do retângulo do
        gráfico — os rótulos do eixo ficam DENTRO dessa faixa reservada
        pelo tight_layout, não logo abaixo dela)."""
        self.fig.tight_layout()
        self.chart_canvas.draw()
        pos = self.ax.get_position()

        # onde o texto do eixo X (tick labels + "Tempo") realmente termina,
        # não só onde o retângulo do gráfico termina
        eixo_x_bbox = self.ax.xaxis.get_tightbbox(self.chart_canvas.get_renderer())
        eixo_x_bbox_fig = eixo_x_bbox.transformed(self.fig.transFigure.inverted())
        zona_eixo = pos.y0 - eixo_x_bbox_fig.y0

        ancora_y = eixo_x_bbox_fig.y0 - GAP_LEGENDA
        legenda = construir_legenda(self.ax, self.fig, tarefas_resultado, cores_recursos, ancora_y)
        tabela_ax, altura_tabela = construir_tabela_resumo(self.fig, resultado, n_trocas, ancora_y)
        self.chart_canvas.draw()

        bbox_fig = legenda.get_window_extent(self.chart_canvas.get_renderer()).transformed(
            self.fig.transFigure.inverted()
        )
        altura_legenda = ancora_y - bbox_fig.y0
        altura_final = max(altura_legenda, altura_tabela)

        topo = pos.y0 + pos.height  # preserva o topo (título etc.) como o tight_layout decidiu
        y0_novo = zona_eixo + GAP_LEGENDA + altura_final + FOLGA_INFERIOR
        self.ax.set_position([pos.x0, y0_novo, pos.width, topo - y0_novo])

        legenda.remove()
        tabela_ax.remove()
        ancora_y = y0_novo - zona_eixo - GAP_LEGENDA
        construir_legenda(self.ax, self.fig, tarefas_resultado, cores_recursos, ancora_y)
        self._tabela_resumo_ax, _ = construir_tabela_resumo(self.fig, resultado, n_trocas, ancora_y)
