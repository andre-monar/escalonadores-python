import tkinter as tk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from algoritmos.fcfs import fcfs
from algoritmos.round_robin import round_robin
from algoritmos.validacoes import ErroValidacao
from models.periodo import TipoPeriodo
from models.resultado import Parametros, ResultadoSimulacao
from models.tarefa import Tarefa
from views import theme
from views.components.widgets import Dropdown, PlaceholderNumericEntry, RoundedButton, ScrollableFrame, TrashIcon

COLUMN_LABELS = ["ID", "Chegada", "", "Duração", "", "Prioridade", "", ""]
# (col_entry, col_unidade, unidade, placeholder/mínimo)
TASK_FIELDS = [(1, 2, "s", 0), (3, 4, "s", 0), (5, 6, "", 1)]

ALGO_FCFS = "FCFS"
ALGO_SJF = "SJF"
ALGO_SRTF = "SRTF"
ALGO_ROUND_ROBIN = "RR"
ALGO_PRIOC = "PRIOc"
ALGO_PRIOP = "PRIOp"

SCHEDULER_OPTIONS = [
    (ALGO_FCFS, "FCFS | First-Come, First-Served"),
    (ALGO_ROUND_ROBIN, "RR | Round-Robin"),
    (ALGO_SJF, "SJF | Shortest Job First"),
    (ALGO_SRTF, "SRTF | Shortest Remaining Time First"),
    (ALGO_PRIOC, "PRIOc | Prioridade Cooperativa"),
    (ALGO_PRIOP, "PRIOp | Prioridade Preemptiva"),
]
ALGORITMOS_DESABILITADOS = {ALGO_SJF, ALGO_SRTF, ALGO_PRIOC, ALGO_PRIOP}
ALGORITMOS_COM_PRIORIDADE = {ALGO_PRIOC, ALGO_PRIOP}

CORRECTION_OPTIONS = ["Nenhum", "Herança", "Teto"]
CORRECTION_DEFAULT = "Nenhum"

CHART_EXECUCAO = theme.PURPLE
CHART_TROCA_CONTEXTO = "#f7b955"

SIDEBAR_WIDTH = 400
SIDEBAR_PAD = 18


class BuildView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=theme.BG)
        self.controller = controller
        self.task_rows = []
        self._next_id = 1

        self._build_topbar()
        self._build_body()

        self._add_task_row()
        self._add_task_row()

    # ---------------------------------------------------------------- topbar
    def _build_topbar(self):
        bar = tk.Frame(self, bg=theme.BG)
        bar.pack(fill="x", padx=24, pady=(20, 10))

        RoundedButton(
            bar, "← Voltar",
            command=lambda: self.controller.show_frame("HomeView"),
            width=110, height=38, bg=theme.BG, hover=theme.CARD_BG,
            fg=theme.TEXT, outline=theme.BORDER,
        ).pack(side="left")

        tk.Label(
            bar, text="Novo Cenário", bg=theme.BG, fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 18, "bold"),
        ).pack(side="left", padx=20)

    # ------------------------------------------------------------------ body
    def _build_body(self):
        body = tk.Frame(self, bg=theme.BG)
        body.pack(fill="both", expand=True)

        self._build_sidebar(body)
        self._build_chart_panel(body)

    def _build_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg=theme.SIDEBAR_BG, width=SIDEBAR_WIDTH)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        content_width = SIDEBAR_WIDTH - 2 * SIDEBAR_PAD

        # botão principal fixo embaixo, fora da área com scroll — sempre visível,
        # não importa o quanto o resto do conteúdo cresça. Empacotado ANTES do
        # scroll (side="bottom" reserva o espaço dele primeiro).
        RoundedButton(
            sidebar, "Gerar gráfico",
            command=self._on_generate_click,
            width=content_width, height=52,
            bg=theme.PURPLE, hover=theme.PURPLE_HOVER,
        ).pack(side="bottom", padx=SIDEBAR_PAD, pady=20)

        # tudo mais fica dentro de uma área com scroll — se a janela ficar baixa
        # demais pro conteúdo inteiro, rola em vez de cortar.
        scroll = ScrollableFrame(sidebar, bg=theme.SIDEBAR_BG)
        scroll.pack(fill="both", expand=True)
        conteudo = scroll.inner

        tk.Label(
            conteudo, text="Algoritmo de escalonador", bg=theme.SIDEBAR_BG, fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 14, "bold"),
        ).pack(anchor="w", padx=SIDEBAR_PAD, pady=(20, 10))

        self.scheduler_dropdown = Dropdown(
            conteudo, SCHEDULER_OPTIONS, initial=ALGO_FCFS,
            width=content_width, height=48, command=self._on_algorithm_change,
            desabilitados=ALGORITMOS_DESABILITADOS,
        )
        self.scheduler_dropdown.pack(padx=SIDEBAR_PAD, pady=(0, 20))

        self._build_specs(conteudo, content_width)

        self.specs_error_label = tk.Label(
            conteudo, text="", bg=theme.SIDEBAR_BG, fg=theme.DANGER,
            font=(theme.FONT_FAMILY, 10), anchor="w", justify="left",
            wraplength=content_width,
        )
        # empacotado já na posição certa (entre Especificações e Tarefas), com
        # padding zerado — _mostrar_erro_specs/_limpar_erro_specs só ajustam o
        # padding depois (pack_configure preserva a posição; um pack() novo não)
        self.specs_error_label.pack(anchor="w", padx=SIDEBAR_PAD, pady=0)

        tk.Label(
            conteudo, text="Tarefas", bg=theme.SIDEBAR_BG, fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 14, "bold"),
        ).pack(anchor="w", padx=SIDEBAR_PAD, pady=(0, 10))

        header = tk.Frame(conteudo, bg=theme.SIDEBAR_BG)
        header.pack(fill="x", padx=SIDEBAR_PAD)
        self._configure_row_columns(header)
        for col, text in enumerate(COLUMN_LABELS):
            tk.Label(
                header, text=text, bg=theme.SIDEBAR_BG, fg=theme.TEXT_MUTED,
                font=(theme.FONT_FAMILY, 9, "bold"), anchor="w",
            ).grid(row=0, column=col, sticky="ew", padx=4)

        self.rows_container = tk.Frame(conteudo, bg=theme.SIDEBAR_BG)
        self.rows_container.pack(fill="x", padx=SIDEBAR_PAD, pady=(6, 14))

        RoundedButton(
            conteudo, "+  Adicionar tarefa",
            command=self._add_task_row,
            width=content_width, height=48, radius=10,
            bg=theme.SURFACE, hover=theme.SURFACE_HOVER,
            fg=theme.TEXT, outline=theme.BORDER,
            font=(theme.FONT_FAMILY, 11, "bold"),
        ).pack(padx=SIDEBAR_PAD, pady=(0, 16))

    def _build_specs(self, sidebar, content_width):
        tk.Label(
            sidebar, text="Especificações", bg=theme.SIDEBAR_BG, fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 14, "bold"),
        ).pack(anchor="w", padx=SIDEBAR_PAD, pady=(0, 10))

        specs = tk.Frame(sidebar, bg=theme.SIDEBAR_BG)
        specs.pack(fill="x", padx=SIDEBAR_PAD, pady=(0, 20))
        specs.grid_columnconfigure(0, weight=1)
        specs.grid_columnconfigure(1, weight=0)
        specs.grid_columnconfigure(2, weight=0, minsize=18)

        self.ctx_label = self._spec_label(specs, "Tempo de troca de contexto")
        self.ctx_entry = PlaceholderNumericEntry(specs, placeholder=0, width=8)
        self.ctx_unit = self._spec_unit(specs, "s")
        self.ctx_label.grid(row=0, column=0, sticky="w", pady=8)
        self.ctx_entry.grid(row=0, column=1, sticky="e", pady=8, ipady=6)
        self.ctx_unit.grid(row=0, column=2, sticky="w", padx=(4, 0))

        self.quantum_label = self._spec_label(specs, "Quantum")
        self.quantum_entry = PlaceholderNumericEntry(specs, placeholder=0, width=8)
        self.quantum_unit = self._spec_unit(specs, "s")

        self.correction_label = self._spec_label(specs, "Protocolo de correção")
        self.correction_dropdown = Dropdown(
            specs, CORRECTION_OPTIONS, initial=CORRECTION_DEFAULT,
            width=150, height=40,
        )

        self._update_specs_visibility()

    @staticmethod
    def _spec_label(parent, text):
        return tk.Label(
            parent, text=text, bg=theme.SIDEBAR_BG, fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 11), anchor="w",
        )

    @staticmethod
    def _spec_unit(parent, text):
        return tk.Label(
            parent, text=text, bg=theme.SIDEBAR_BG, fg=theme.TEXT_MUTED,
            font=(theme.FONT_FAMILY, 9),
        )

    def _on_algorithm_change(self, _value):
        self._update_specs_visibility()
        self._update_priority_lock()
        self._limpar_erro_specs()

    def _mostrar_erro_specs(self, mensagem):
        self.specs_error_label.config(text=mensagem)
        self.specs_error_label.pack_configure(pady=(0, 14))

    def _limpar_erro_specs(self):
        self.specs_error_label.config(text="")
        self.specs_error_label.pack_configure(pady=0)

    def _update_specs_visibility(self):
        algoritmo = self.scheduler_dropdown.get()

        if algoritmo == ALGO_ROUND_ROBIN:
            self.quantum_label.grid(row=1, column=0, sticky="w", pady=8)
            self.quantum_entry.grid(row=1, column=1, sticky="e", pady=8, ipady=6)
            self.quantum_unit.grid(row=1, column=2, sticky="w", padx=(4, 0))
        else:
            self.quantum_label.grid_remove()
            self.quantum_entry.grid_remove()
            self.quantum_unit.grid_remove()

        if algoritmo == ALGO_PRIOP:
            self.correction_label.grid(row=2, column=0, sticky="w", pady=8)
            self.correction_dropdown.grid(row=2, column=1, sticky="e", pady=8)
        else:
            self.correction_label.grid_remove()
            self.correction_dropdown.grid_remove()

    def _update_priority_lock(self):
        travar = self.scheduler_dropdown.get() not in ALGORITMOS_COM_PRIORIDADE
        for row in self.task_rows:
            row["prioridade_entry"].set_locked(travar)

    @staticmethod
    def _configure_row_columns(row):
        row.grid_columnconfigure(0, weight=0, minsize=26)   # ID
        row.grid_columnconfigure(1, weight=1)                # Chegada
        row.grid_columnconfigure(2, weight=0, minsize=16)    # unidade
        row.grid_columnconfigure(3, weight=1)                # Duração
        row.grid_columnconfigure(4, weight=0, minsize=16)    # unidade
        row.grid_columnconfigure(5, weight=1)                # Prioridade
        row.grid_columnconfigure(6, weight=0, minsize=16)    # unidade
        row.grid_columnconfigure(7, weight=0, minsize=34)    # lixeira

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

    # ------------------------------------------------------------- CRUD rows
    def _add_task_row(self):
        row_id = self._next_id
        self._next_id += 1

        row = tk.Frame(self.rows_container, bg=theme.SIDEBAR_BG)
        row.pack(fill="x", pady=5)
        self._configure_row_columns(row)

        id_label = tk.Label(
            row, text=str(row_id), bg=theme.SIDEBAR_BG, fg=theme.TEXT_MUTED,
            font=(theme.FONT_FAMILY, 10), anchor="w",
        )
        id_label.grid(row=0, column=0, sticky="ew", padx=4)

        entries = []
        for col_entry, col_unidade, unidade, placeholder in TASK_FIELDS:
            entry = PlaceholderNumericEntry(row, placeholder=placeholder)
            entry.grid(row=0, column=col_entry, sticky="ew", padx=4, ipady=8)
            entries.append(entry)

            tk.Label(
                row, text=unidade, bg=theme.SIDEBAR_BG, fg=theme.TEXT_MUTED,
                font=(theme.FONT_FAMILY, 9),
            ).grid(row=0, column=col_unidade, sticky="w")

        remove_btn = TrashIcon(row, command=lambda: self._remove_task_row(entry_data), size=22)
        remove_btn.grid(row=0, column=7, sticky="e", padx=4)

        prioridade_entry = entries[2]
        prioridade_entry.set_locked(self.scheduler_dropdown.get() not in ALGORITMOS_COM_PRIORIDADE)

        entry_data = {
            "frame": row, "id_label": id_label, "entries": entries,
            "prioridade_entry": prioridade_entry,
        }
        self.task_rows.append(entry_data)

    def _remove_task_row(self, entry_data):
        if len(self.task_rows) <= 1:
            return
        entry_data["frame"].destroy()
        self.task_rows.remove(entry_data)
        self._renumber_rows()

    def _renumber_rows(self):
        for index, row in enumerate(self.task_rows, start=1):
            row["id_label"].config(text=str(index))

    # --------------------------------------------------------- monta objetos
    def _build_tarefas(self) -> list[Tarefa]:
        tarefas = []
        for index, row in enumerate(self.task_rows, start=1):
            chegada_entry, duracao_entry, prioridade_entry = row["entries"]
            tarefas.append(Tarefa(
                id=index,
                chegada=chegada_entry.get_value(),
                tp=duracao_entry.get_value(),
                prioridade=prioridade_entry.get_value(),
            ))
        return tarefas

    def _build_parametros(self) -> Parametros:
        algoritmo = self.scheduler_dropdown.get()

        quantum = self.quantum_entry.get_value() if algoritmo == ALGO_ROUND_ROBIN else None

        protocolo = None
        if algoritmo == ALGO_PRIOP:
            selecionado = self.correction_dropdown.get()
            protocolo = None if selecionado == "Nenhum" else selecionado

        return Parametros(
            algoritmo=algoritmo,
            ctx_time=self.ctx_entry.get_value(),
            quantum=quantum,
            protocolo=protocolo,
        )

    def _on_generate_click(self):
        tarefas = self._build_tarefas()
        parametros = self._build_parametros()

        try:
            if parametros.algoritmo == ALGO_FCFS:
                resultado = fcfs(tarefas, ctx_time=parametros.ctx_time)
            elif parametros.algoritmo == ALGO_ROUND_ROBIN:
                resultado = round_robin(tarefas, ctx_time=parametros.ctx_time, quantum=parametros.quantum)
            else:
                return  # os outros algoritmos ainda não estão implementados
        except ErroValidacao as erro:
            self._mostrar_erro_specs(str(erro))
            return

        self._limpar_erro_specs()
        self._desenhar_resultado(resultado)

    # -------------------------------------------------------------- chart
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

    def _desenhar_resultado(self, resultado: ResultadoSimulacao):
        self.ax.clear()
        self._style_axes()

        tarefas_resultado = sorted(resultado.tarefas.values(), key=lambda tr: tr.tarefa.id)
        tempo_max = max(periodo.fim for tr in tarefas_resultado for periodo in tr.periodos)

        for tr in tarefas_resultado:
            for periodo in tr.periodos:
                cor = CHART_EXECUCAO if periodo.tipo == TipoPeriodo.EXECUCAO else CHART_TROCA_CONTEXTO
                self.ax.barh(
                    tr.tarefa.id, periodo.fim - periodo.inicio, left=periodo.inicio,
                    color=cor, edgecolor=theme.CARD_BG, height=0.55,
                )
                if periodo.preemptado_por_quantum:
                    self.ax.plot(
                        [periodo.fim, periodo.fim], [tr.tarefa.id - 0.32, tr.tarefa.id + 0.32],
                        linestyle="--", color=theme.TEXT, linewidth=1.2,
                    )
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
