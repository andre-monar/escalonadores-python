import random
import tkinter as tk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from views import theme
from views.components.widgets import Dropdown, PlaceholderNumericEntry, RoundedButton, ScrollableFrame, TrashIcon

COLUMN_LABELS = ["ID", "Chegada", "", "Duração", "", "Prioridade", "", ""]
# (col_entry, col_unidade, unidade, placeholder/mínimo)
TASK_FIELDS = [(1, 2, "s", 0), (3, 4, "s", 0), (5, 6, "", 1)]
CHART_COLORS = [theme.PURPLE, "#4f9dff", "#38d9a9", "#f7b955", "#ff6b6b", "#c084fc"]

SCHEDULER_OPTIONS = [
    "FCFS",
    "SJF",
    "SRTF",
    "Round-Robin",
    "Prioridade Cooperativa",
    "Prioridade Preemptiva",
]

ALGO_ROUND_ROBIN = "Round-Robin"
ALGO_PRIOP = "Prioridade Preemptiva"
CORRECTION_OPTIONS = ["Nenhum", "Herança", "Teto"]
CORRECTION_DEFAULT = "Nenhum"

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

        tk.Label(
            sidebar, text="Algoritmo de escalonador", bg=theme.SIDEBAR_BG, fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 14, "bold"),
        ).pack(anchor="w", padx=SIDEBAR_PAD, pady=(20, 10))

        self.scheduler_dropdown = Dropdown(
            sidebar, SCHEDULER_OPTIONS, initial=SCHEDULER_OPTIONS[0],
            width=content_width, height=48, command=self._on_algorithm_change,
        )
        self.scheduler_dropdown.pack(padx=SIDEBAR_PAD, pady=(0, 20))

        self._build_specs(sidebar, content_width)

        tk.Label(
            sidebar, text="Tarefas", bg=theme.SIDEBAR_BG, fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 14, "bold"),
        ).pack(anchor="w", padx=SIDEBAR_PAD, pady=(0, 10))

        header = tk.Frame(sidebar, bg=theme.SIDEBAR_BG)
        header.pack(fill="x", padx=SIDEBAR_PAD)
        self._configure_row_columns(header)
        for col, text in enumerate(COLUMN_LABELS):
            tk.Label(
                header, text=text, bg=theme.SIDEBAR_BG, fg=theme.TEXT_MUTED,
                font=(theme.FONT_FAMILY, 9, "bold"), anchor="w",
            ).grid(row=0, column=col, sticky="ew", padx=4)

        scroll = ScrollableFrame(sidebar, bg=theme.SIDEBAR_BG)
        scroll.pack(fill="both", expand=True, padx=SIDEBAR_PAD, pady=(6, 14))
        self.rows_container = scroll.inner

        RoundedButton(
            sidebar, "+  Adicionar tarefa",
            command=self._add_task_row,
            width=content_width, height=48, radius=10,
            bg=theme.SURFACE, hover=theme.SURFACE_HOVER,
            fg=theme.TEXT, outline=theme.BORDER,
            font=(theme.FONT_FAMILY, 11, "bold"),
        ).pack(padx=SIDEBAR_PAD, pady=(0, 16))

        RoundedButton(
            sidebar, "Gerar gráfico",
            command=self._draw_placeholder_chart,
            width=content_width, height=52,
            bg=theme.PURPLE, hover=theme.PURPLE_HOVER,
        ).pack(side="bottom", padx=SIDEBAR_PAD, pady=20)

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
        card.pack(fill="both", expand=True, padx=30, pady=30)

        self.fig = Figure(figsize=(6, 5), dpi=100, facecolor=theme.CARD_BG)
        self.ax = self.fig.add_subplot(111)

        self.chart_canvas = FigureCanvasTkAgg(self.fig, master=card)
        self.chart_canvas.get_tk_widget().configure(bg=theme.CARD_BG, highlightthickness=0)
        self.chart_canvas.get_tk_widget().pack(fill="both", expand=True, padx=16, pady=16)

        self._draw_placeholder_chart()

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

        entry_data = {"frame": row, "id_label": id_label, "entries": entries}
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

    # -------------------------------------------------------------- chart
    def _style_axes(self):
        self.ax.set_facecolor(theme.CARD_BG)
        self.ax.tick_params(colors=theme.TEXT_MUTED, labelsize=9)
        for spine in self.ax.spines.values():
            spine.set_color(theme.BORDER)
        self.ax.xaxis.label.set_color(theme.TEXT_MUTED)
        self.ax.title.set_color(theme.TEXT)

    def _draw_placeholder_chart(self):
        self.ax.clear()
        self._style_axes()

        n = max(len(self.task_rows), 1)
        t = 0
        for i in range(n):
            duracao = random.randint(2, 6)
            color = CHART_COLORS[i % len(CHART_COLORS)]
            self.ax.barh(i + 1, duracao, left=t, color=color,
                         edgecolor=theme.CARD_BG, height=0.55)
            t += duracao + random.choice([0, 1])

        self.ax.set_yticks(range(1, n + 1))
        self.ax.set_yticklabels([f"Tarefa {i + 1}" for i in range(n)], color=theme.TEXT)
        self.ax.set_xlabel("Tempo")
        self.ax.set_title("Pré-visualização (dados fictícios)", fontsize=11)

        self.fig.tight_layout()
        self.chart_canvas.draw()
