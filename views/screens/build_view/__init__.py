import tkinter as tk

from algoritmos.fcfs import fcfs
from algoritmos.priop import priop
from algoritmos.prioc import prioc
from algoritmos.round_robin import round_robin
from algoritmos.sjf import sjf
from algoritmos.srtf import srtf
from algoritmos.validacoes import ErroValidacao
from models.resultado import Parametros
from views import theme
from views.components.dropdown import Dropdown
from views.components.rounded_button import RoundedButton
from views.components.scrollable_frame import ScrollableFrame
from views.screens.build_view.cenario import CenarioMixin
from views.screens.build_view.chart import ChartMixin
from views.screens.build_view.constants import (
    ALGO_FCFS,
    ALGO_PRIOC,
    ALGO_PRIOP,
    ALGO_ROUND_ROBIN,
    ALGO_SJF,
    ALGO_SRTF,
    ALGORITMOS_DESABILITADOS,
    SCHEDULER_OPTIONS,
    SIDEBAR_PAD,
    SIDEBAR_WIDTH,
)
from views.screens.build_view.recursos import RecursosMixin
from views.screens.build_view.specs import SpecsMixin
from views.screens.build_view.tarefas import TarefasMixin


class BuildView(RecursosMixin, TarefasMixin, SpecsMixin, ChartMixin, CenarioMixin, tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=theme.BG)
        self.controller = controller
        self.task_rows = []
        self.resource_rows = []

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

        # botões fixos embaixo, fora da área com scroll — sempre visíveis, não
        # importa o quanto o resto do conteúdo cresça. Empacotados ANTES do
        # scroll (side="bottom" reserva o espaço deles primeiro). O primeiro
        # empacotado com side="bottom" fica mais embaixo — por isso "Salvar
        # cenário" vem antes no código, pra ficar abaixo de "Gerar gráfico".
        RoundedButton(
            sidebar, "Salvar cenário",
            command=self._on_save_click,
            width=content_width, height=44,
            bg=theme.SURFACE, hover=theme.SURFACE_HOVER,
            fg=theme.TEXT, outline=theme.BORDER,
            font=(theme.FONT_FAMILY, 11, "bold"),
        ).pack(side="bottom", padx=SIDEBAR_PAD, pady=(0, 20))

        RoundedButton(
            sidebar, "Gerar gráfico",
            command=self._on_generate_click,
            width=content_width, height=52,
            bg=theme.PURPLE, hover=theme.PURPLE_HOVER,
        ).pack(side="bottom", padx=SIDEBAR_PAD, pady=(20, 10))

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
        self._build_resources(conteudo, content_width)
        self._build_tasks_section(conteudo, content_width)

    def _on_algorithm_change(self, _value):
        self._update_specs_visibility()
        self._update_priority_lock()
        self._update_resources_visibility()
        self._limpar_erro_specs()

    # --------------------------------------------------------- monta objetos
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
        tem_tarefa_valida = any(row["entries"][1].get_value() > 0 for row in self.task_rows)
        if not tem_tarefa_valida:
            self._mostrar_erro_tarefas("Nenhuma tarefa tem duração válida")
            return
        self._limpar_erro_tarefas()
        self._limpar_tarefas_invalidas()

        tarefas = self._build_tarefas()
        parametros = self._build_parametros()

        try:
            if parametros.algoritmo == ALGO_FCFS:
                resultado = fcfs(tarefas, ctx_time=parametros.ctx_time)
            elif parametros.algoritmo == ALGO_ROUND_ROBIN:
                resultado = round_robin(tarefas, ctx_time=parametros.ctx_time, quantum=parametros.quantum)
            elif parametros.algoritmo == ALGO_SJF:
                resultado = sjf(tarefas, ctx_time=parametros.ctx_time)
            elif parametros.algoritmo == ALGO_SRTF:
                resultado = srtf(tarefas, ctx_time=parametros.ctx_time)
            elif parametros.algoritmo == ALGO_PRIOC:
                resultado = prioc(tarefas, ctx_time=parametros.ctx_time)
            elif parametros.algoritmo == ALGO_PRIOP:
                resultado = priop(tarefas, ctx_time=parametros.ctx_time, protocolo=parametros.protocolo)
            else:
                return  # os outros algoritmos ainda não estão implementados
        except ErroValidacao as erro:
            self._mostrar_erro_specs(str(erro))
            return

        self._limpar_erro_specs()
        self._desenhar_resultado(resultado)
