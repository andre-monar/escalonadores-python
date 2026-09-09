import json
import tkinter as tk
from tkinter import filedialog

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from algoritmos.fcfs import fcfs
from algoritmos.round_robin import round_robin
from algoritmos.sjf import sjf
from algoritmos.prioc import prioc
from algoritmos.priop import priop
from algoritmos.srtf import srtf
from algoritmos.validacoes import ErroValidacao
from models.periodo import TipoPeriodo
from models.resultado import Parametros, ResultadoSimulacao
from models.tarefa import Tarefa
from views import theme
from views.components.widgets import (
    ColorPickerButton, Dropdown, PlaceholderNumericEntry, RoundedButton, ScrollableFrame, TrashIcon,
)

COLUMN_LABELS = ["ID", "Chegada", "", "Duração", "", "Prioridade", "", ""]
# (col_entry, col_unidade, unidade, placeholder/mínimo)
TASK_FIELDS = [(1, 2, "s", 0), (3, 4, "s", 0), (5, 6, "", 1)]

RESOURCE_COLUMN_LABELS = ["ID", "Cor", "Configurar", ""]
RESOURCE_COLORS = [
    "#ff6b6b", "#ffa94d", "#ffd43b", "#69db7c", "#38d9a9",
    "#4dabf7", "#748ffc", "#9775fa", "#f783ac", "#ced4da",
]

VINCULO_COLUMN_LABELS = [
    "Tarefa", "T.Ini\n(Tarefa)", "T.Ini\n(Recurso)", "T.Fim\n(Recurso)", "T.Fim\n(Tarefa)", "",
]

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
ALGORITMOS_DESABILITADOS = set()
ALGORITMOS_COM_PRIORIDADE = {ALGO_PRIOC, ALGO_PRIOP}

CORRECTION_OPTIONS = ["Nenhum", "Herança", "Teto"]
CORRECTION_DEFAULT = "Nenhum"

CHART_EXECUCAO = theme.PURPLE
CHART_TROCA_CONTEXTO = "#f7b955"
CHART_ESPERA = theme.PURPLE_DARK  # mesma borda da execução/troca, só que vazada (sem preenchimento)

SIDEBAR_WIDTH = 400
SIDEBAR_PAD = 18


def validar_cenario(cenario) -> bool:
    """Confere se um dict lido de um .json tem a cara de um cenário salvo por
    essa tela — usado pelo HomeView antes de tentar carregar (R2: rejeitar
    arquivo inválido em vez de deixar a tela num estado quebrado)."""
    if not isinstance(cenario, dict):
        return False

    algoritmos_validos = {valor for valor, _ in SCHEDULER_OPTIONS}
    if cenario.get("algoritmo") not in algoritmos_validos:
        return False
    if cenario.get("protocolo_correcao") not in CORRECTION_OPTIONS:
        return False
    if not isinstance(cenario.get("ctx_time"), (int, float)):
        return False
    if not isinstance(cenario.get("quantum"), (int, float)):
        return False

    tarefas = cenario.get("tarefas")
    if not isinstance(tarefas, list):
        return False
    for tarefa in tarefas:
        if not isinstance(tarefa, dict):
            return False
        for chave in ("chegada", "duracao", "prioridade"):
            if not isinstance(tarefa.get(chave), (int, float)):
                return False

    return True


class BuildView(tk.Frame):
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

        self.specs_error_label = tk.Label(
            conteudo, text="", bg=theme.SIDEBAR_BG, fg=theme.DANGER,
            font=(theme.FONT_FAMILY, 10), anchor="w", justify="left",
            wraplength=content_width,
        )
        # empacotado já na posição certa (entre Especificações e Tarefas), com
        # padding zerado — _mostrar_erro_specs/_limpar_erro_specs só ajustam o
        # padding depois (pack_configure preserva a posição; um pack() novo não)
        self.specs_error_label.pack(anchor="w", padx=SIDEBAR_PAD, pady=0)

        self._build_resources(conteudo, content_width)

        self._tarefas_titulo = tk.Label(
            conteudo, text="Tarefas", bg=theme.SIDEBAR_BG, fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 14, "bold"),
        )
        self._tarefas_titulo.pack(anchor="w", padx=SIDEBAR_PAD, pady=(0, 10))

        RoundedButton(
            conteudo, "Abrir cenário",
            command=self._on_open_scenario_click,
            width=content_width, height=48, radius=10,
            bg=theme.SURFACE, hover=theme.SURFACE_HOVER,
            fg=theme.TEXT, outline=theme.BORDER,
            font=(theme.FONT_FAMILY, 11, "bold"),
        ).pack(padx=SIDEBAR_PAD, pady=(0, 10))

        self.tasks_error_label = tk.Label(
            conteudo, text="", bg=theme.SIDEBAR_BG, fg=theme.DANGER,
            font=(theme.FONT_FAMILY, 10), anchor="w", justify="left",
            wraplength=content_width,
        )
        self.tasks_error_label.pack(anchor="w", padx=SIDEBAR_PAD, pady=0)

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

    def _build_resources(self, sidebar, content_width):
        # a seção inteira (título, tabela, botão) só aparece pro PRIOp — é
        # onde entram os recursos compartilhados pra seção crítica (R5-R7).
        self.resources_section = tk.Frame(sidebar, bg=theme.SIDEBAR_BG)

        tk.Label(
            self.resources_section, text="Recursos", bg=theme.SIDEBAR_BG, fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 14, "bold"),
        ).pack(anchor="w", padx=SIDEBAR_PAD, pady=(0, 10))

        header = tk.Frame(self.resources_section, bg=theme.SIDEBAR_BG)
        header.pack(fill="x", padx=SIDEBAR_PAD)
        self._configure_resource_row_columns(header)
        for col, text in enumerate(RESOURCE_COLUMN_LABELS):
            tk.Label(
                header, text=text, bg=theme.SIDEBAR_BG, fg=theme.TEXT_MUTED,
                font=(theme.FONT_FAMILY, 9, "bold"), anchor="w",
            ).grid(row=0, column=col, sticky="ew", padx=4)

        self.resource_rows_container = tk.Frame(self.resources_section, bg=theme.SIDEBAR_BG)
        self.resource_rows_container.pack(fill="x", padx=SIDEBAR_PAD, pady=(6, 14))

        RoundedButton(
            self.resources_section, "+  Adicionar recurso",
            command=self._add_resource_row,
            width=content_width, height=48, radius=10,
            bg=theme.SURFACE, hover=theme.SURFACE_HOVER,
            fg=theme.TEXT, outline=theme.BORDER,
            font=(theme.FONT_FAMILY, 11, "bold"),
        ).pack(padx=SIDEBAR_PAD, pady=(0, 16))

        self._update_resources_visibility()

    def _update_resources_visibility(self):
        if self.scheduler_dropdown.get() == ALGO_PRIOP:
            self.resources_section.pack(anchor="w", fill="x", before=self._tarefas_titulo)
        else:
            self.resources_section.pack_forget()

    @staticmethod
    def _configure_resource_row_columns(row):
        row.grid_columnconfigure(0, weight=0, minsize=26)   # ID (mesmo tamanho de Tarefas)
        row.grid_columnconfigure(1, weight=0, minsize=40)    # Cor
        row.grid_columnconfigure(2, weight=1)                # Configurar
        row.grid_columnconfigure(3, weight=0, minsize=34)    # lixeira

    def _add_resource_row(self):
        row = tk.Frame(self.resource_rows_container, bg=theme.SIDEBAR_BG)
        row.pack(fill="x", pady=5)
        self._configure_resource_row_columns(row)

        id_label = tk.Label(
            row, text=str(len(self.resource_rows) + 1), bg=theme.SIDEBAR_BG, fg=theme.TEXT_MUTED,
            font=(theme.FONT_FAMILY, 10), anchor="w",
        )
        id_label.grid(row=0, column=0, sticky="ew", padx=4)

        cor_picker = ColorPickerButton(row, RESOURCE_COLORS, size=28)
        cor_picker.grid(row=0, column=1, sticky="w", padx=4)

        entry_data = {
            "frame": row, "id_label": id_label, "cor_picker": cor_picker,
            "vinculos": [], "popup": None,
            "popup_click_binding": None, "popup_unmap_binding": None,
        }

        configurar_btn = RoundedButton(
            row, "Configurar",
            command=lambda: self._abrir_configurar_recurso(entry_data),
            width=110, height=36, radius=10,
            bg=theme.SURFACE, hover=theme.SURFACE_HOVER,
            fg=theme.TEXT, outline=theme.BORDER,
            font=(theme.FONT_FAMILY, 10, "bold"),
        )
        configurar_btn.grid(row=0, column=2, sticky="ew", padx=4)
        entry_data["configurar_btn"] = configurar_btn

        remove_btn = TrashIcon(row, command=lambda: self._remove_resource_row(entry_data), size=22)
        remove_btn.grid(row=0, column=3, sticky="e", padx=4)

        self.resource_rows.append(entry_data)

    def _remove_resource_row(self, entry_data):
        self._fechar_configurar_recurso(entry_data)
        entry_data["frame"].destroy()
        self.resource_rows.remove(entry_data)
        self._renumber_resource_rows()

    def _renumber_resource_rows(self):
        for index, row in enumerate(self.resource_rows, start=1):
            row["id_label"].config(text=str(index))

    # -------------------------------------------------- configurar recurso
    def _tarefas_disponiveis(self):
        """Opções pro dropdown "vincular tarefa" — sempre recalculado na hora
        de abrir, pra refletir as tarefas que existem AGORA (podem ter mudado
        desde a última vez que esse popup foi aberto)."""
        return [(indice, f"Tarefa {indice}") for indice in range(1, len(self.task_rows) + 1)]

    def _abrir_configurar_recurso(self, recurso):
        if recurso["popup"] is not None:
            self._fechar_configurar_recurso(recurso)
            return

        if not recurso["vinculos"]:
            recurso["vinculos"].append({"tarefa_index": None, "t_inicial_recurso": 0, "t_final_recurso": 0})

        botao = recurso["configurar_btn"]
        x = botao.winfo_rootx()
        y = botao.winfo_rooty() + botao.winfo_height() + 4

        popup = tk.Toplevel(self)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(bg=theme.BORDER)

        inner = tk.Frame(popup, bg=theme.CARD_BG)
        inner.pack(padx=1, pady=1)

        popup_state = {"recurso": recurso, "rows_container": None}

        header = tk.Frame(inner, bg=theme.CARD_BG)
        header.pack(padx=10, pady=(10, 4))
        self._configure_vinculo_row_columns(header)
        for col, texto in enumerate(VINCULO_COLUMN_LABELS):
            tk.Label(
                header, text=texto, bg=theme.CARD_BG, fg=theme.TEXT_MUTED,
                font=(theme.FONT_FAMILY, 8, "bold"), justify="center",
            ).grid(row=0, column=col, sticky="ew", padx=3)

        rows_container = tk.Frame(inner, bg=theme.CARD_BG)
        rows_container.pack(padx=10)
        popup_state["rows_container"] = rows_container

        for vinculo in recurso["vinculos"]:
            self._renderizar_vinculo_row(popup_state, vinculo)

        rodape = tk.Frame(inner, bg=theme.CARD_BG)
        rodape.pack(padx=10, pady=10)

        RoundedButton(
            rodape, "+  Adicionar vínculo",
            command=lambda: self._adicionar_vinculo(popup_state),
            width=200, height=34, radius=8,
            bg=theme.SURFACE, hover=theme.SURFACE_HOVER,
            fg=theme.TEXT, outline=theme.BORDER,
            font=(theme.FONT_FAMILY, 10, "bold"),
        ).pack(side="left")

        RoundedButton(
            rodape, "Fechar",
            command=lambda: self._fechar_configurar_recurso(recurso),
            width=90, height=34, radius=8,
            bg=theme.SURFACE, hover=theme.SURFACE_HOVER,
            fg=theme.TEXT, outline=theme.BORDER,
            font=(theme.FONT_FAMILY, 10, "bold"),
        ).pack(side="left", padx=(8, 0))

        popup.update_idletasks()
        popup.geometry(f"+{x}+{y}")

        recurso["popup"] = popup
        root = self.winfo_toplevel()
        recurso["popup_click_binding"] = root.bind(
            "<Button-1>", lambda e: self._on_configurar_popup_click(e, recurso), add="+",
        )
        recurso["popup_unmap_binding"] = root.bind(
            "<Unmap>", lambda _e: self._fechar_configurar_recurso(recurso), add="+",
        )

    def _on_configurar_popup_click(self, event, recurso):
        popup = recurso["popup"]
        if popup is None:
            return
        widget = self.winfo_containing(event.x_root, event.y_root)
        node = widget
        while node is not None:
            if node in (popup, recurso["configurar_btn"]):
                return
            node = getattr(node, "master", None)
        self._fechar_configurar_recurso(recurso)

    def _fechar_configurar_recurso(self, recurso):
        if recurso["popup"] is not None:
            recurso["popup"].destroy()
            recurso["popup"] = None
        root = self.winfo_toplevel()
        if recurso["popup_click_binding"] is not None:
            root.unbind("<Button-1>", recurso["popup_click_binding"])
            recurso["popup_click_binding"] = None
        if recurso["popup_unmap_binding"] is not None:
            root.unbind("<Unmap>", recurso["popup_unmap_binding"])
            recurso["popup_unmap_binding"] = None

    @staticmethod
    def _configure_vinculo_row_columns(row):
        row.grid_columnconfigure(0, weight=0, minsize=120)  # vincular tarefa
        row.grid_columnconfigure(1, weight=0, minsize=52)    # t. inicial tarefa
        row.grid_columnconfigure(2, weight=0, minsize=52)    # t. inicial recurso
        row.grid_columnconfigure(3, weight=0, minsize=52)    # t. final recurso
        row.grid_columnconfigure(4, weight=0, minsize=52)    # t. final tarefa
        row.grid_columnconfigure(5, weight=0, minsize=26)    # lixeira

    def _renderizar_vinculo_row(self, popup_state, vinculo):
        wrapper = tk.Frame(popup_state["rows_container"], bg=theme.CARD_BG)
        wrapper.pack(fill="x", pady=3)

        row = tk.Frame(wrapper, bg=theme.CARD_BG)
        row.pack(fill="x")
        self._configure_vinculo_row_columns(row)

        # se a tarefa vinculada foi apagada nesse meio tempo, trata como se
        # não tivesse vínculo — evita estourar índice fora do range.
        if vinculo["tarefa_index"] is not None and vinculo["tarefa_index"] > len(self.task_rows):
            vinculo["tarefa_index"] = None

        # o erro vermelho não sobrevive a fechar/reabrir o popup — só some
        # sozinho ao editar de novo ENQUANTO a tela tá aberta.
        vinculo["erro_vermelho"] = None

        dropdown = Dropdown(
            row, self._tarefas_disponiveis(), initial=vinculo["tarefa_index"],
            width=120, height=32, parent_bg=theme.CARD_BG,
            placeholder="Selecionar",
            options_provider=self._tarefas_disponiveis,
            command=lambda valor: self._on_vinculo_tarefa_selecionada(popup_state, vinculo, valor),
        )
        dropdown.grid(row=0, column=0, sticky="w", padx=3)

        t_inicial_tarefa = PlaceholderNumericEntry(row, placeholder=0, width=6)
        t_inicial_tarefa.grid(row=0, column=1, sticky="ew", padx=3, ipady=4)
        t_inicial_tarefa.set_locked(True)

        t_inicial_recurso = PlaceholderNumericEntry(row, placeholder=0, width=6)
        t_inicial_recurso.grid(row=0, column=2, sticky="ew", padx=3, ipady=4)

        t_final_recurso = PlaceholderNumericEntry(row, placeholder=0, width=6)
        t_final_recurso.grid(row=0, column=3, sticky="ew", padx=3, ipady=4)

        t_final_tarefa = PlaceholderNumericEntry(row, placeholder=0, width=6)
        t_final_tarefa.grid(row=0, column=4, sticky="ew", padx=3, ipady=4)
        t_final_tarefa.set_locked(True)

        remove_btn = TrashIcon(row, command=lambda: self._remover_vinculo(popup_state, vinculo), size=18)
        remove_btn.grid(row=0, column=5, sticky="e", padx=3)

        msg_label = tk.Label(
            wrapper, text="", bg=theme.CARD_BG,
            font=(theme.FONT_FAMILY, 8), anchor="w", justify="left",
        )
        # não empacotado aqui — só aparece quando tiver algo a avisar
        # (_mostrar_msg_vinculo/_limpar_msg_vinculo cuidam do pack/pack_forget)

        vinculo["frame"] = wrapper
        vinculo["msg_label"] = msg_label
        vinculo["dropdown"] = dropdown
        vinculo["t_inicial_tarefa_entry"] = t_inicial_tarefa
        vinculo["t_inicial_recurso_entry"] = t_inicial_recurso
        vinculo["t_final_recurso_entry"] = t_final_recurso
        vinculo["t_final_tarefa_entry"] = t_final_tarefa

        if vinculo["tarefa_index"] is not None:
            tp = self.task_rows[vinculo["tarefa_index"] - 1]["entries"][1].get_value()
            t_inicial_tarefa.set_value(0)
            t_final_tarefa.set_value(tp)
            t_inicial_recurso.set_locked(False)
            t_inicial_recurso.set_value(vinculo["t_inicial_recurso"])
            t_final_recurso.set_locked(False)
            t_final_recurso.set_value(vinculo["t_final_recurso"])
            self._renderizar_msg_vinculo(vinculo)
        else:
            t_inicial_recurso.set_locked(True)
            t_final_recurso.set_locked(True)

        t_inicial_recurso.bind(
            "<FocusOut>", lambda _e, v=vinculo: self._validar_vinculo_tempo(v, "inicio"), add="+",
        )
        t_final_recurso.bind(
            "<FocusOut>", lambda _e, v=vinculo: self._validar_vinculo_tempo(v, "fim"), add="+",
        )
        for entry in (t_inicial_recurso, t_final_recurso):
            entry.bind("<Key>", lambda _e, v=vinculo: self._limpar_erro_vermelho_vinculo(v), add="+")

    def _adicionar_vinculo(self, popup_state):
        vinculo = {"tarefa_index": None, "t_inicial_recurso": 0, "t_final_recurso": 0}
        popup_state["recurso"]["vinculos"].append(vinculo)
        self._renderizar_vinculo_row(popup_state, vinculo)

    def _remover_vinculo(self, popup_state, vinculo):
        vinculo["frame"].destroy()
        popup_state["recurso"]["vinculos"].remove(vinculo)

    def _on_vinculo_tarefa_selecionada(self, popup_state, vinculo, indice_tarefa):
        tp = self.task_rows[indice_tarefa - 1]["entries"][1].get_value()

        vinculo["tarefa_index"] = indice_tarefa
        vinculo["t_inicial_recurso"] = 0
        vinculo["t_final_recurso"] = tp
        vinculo["erro_vermelho"] = None

        vinculo["t_inicial_tarefa_entry"].set_value(0)
        vinculo["t_final_tarefa_entry"].set_value(tp)

        vinculo["t_inicial_recurso_entry"].set_locked(False)
        vinculo["t_inicial_recurso_entry"].set_value(0)

        vinculo["t_final_recurso_entry"].set_locked(False)
        vinculo["t_final_recurso_entry"].set_value(tp)

        self._renderizar_msg_vinculo(vinculo)

    def _validar_vinculo_tempo(self, vinculo, campo):
        if vinculo["tarefa_index"] is None:
            return  # nenhuma tarefa vinculada ainda, nada pra validar

        tp = self.task_rows[vinculo["tarefa_index"] - 1]["entries"][1].get_value()
        inicio = vinculo["t_inicial_recurso_entry"].get_value()
        fim = vinculo["t_final_recurso_entry"].get_value()

        # único bloqueio de verdade: início tem que ser MENOR que fim
        # (inválido só se início > fim — empate é permitido). Um vínculo que
        # ultrapassa o tp da tarefa não é travado aqui — a tarefa pode mudar
        # de duração depois, e não queremos truncar nada, só avisar (aviso
        # amarelo, calculado em _renderizar_msg_vinculo).
        if inicio > fim:
            # reverte só o campo que causou o problema, pro padrão natural dele
            if campo == "inicio":
                vinculo["t_inicial_recurso_entry"].set_value(0)
            else:
                vinculo["t_final_recurso_entry"].set_value(tp)
            vinculo["erro_vermelho"] = "Tempo inicial do recurso deve ser menor que o final"
            self._renderizar_msg_vinculo(vinculo)
            return

        vinculo["t_inicial_recurso"] = vinculo["t_inicial_recurso_entry"].get_value()
        vinculo["t_final_recurso"] = vinculo["t_final_recurso_entry"].get_value()
        self._renderizar_msg_vinculo(vinculo)

    def _limpar_erro_vermelho_vinculo(self, vinculo):
        """No <Key>: some com o erro vermelho assim que o usuário começa a
        editar de novo — diferente do aviso amarelo, que é recalculado (some
        só quando a condição em si for corrigida)."""
        if vinculo["erro_vermelho"]:
            vinculo["erro_vermelho"] = None
            self._renderizar_msg_vinculo(vinculo)

    def _renderizar_msg_vinculo(self, vinculo):
        """Decide o que mostrar embaixo da linha do vínculo: erro vermelho
        (bloqueio, tem prioridade) > aviso amarelo (vínculo excede o tp da
        tarefa, não bloqueia) > nada."""
        if vinculo["erro_vermelho"]:
            self._mostrar_msg_vinculo(vinculo, vinculo["erro_vermelho"], theme.DANGER)
            return

        tp = self.task_rows[vinculo["tarefa_index"] - 1]["entries"][1].get_value()
        if vinculo["t_final_recurso"] > tp:
            self._mostrar_msg_vinculo(vinculo, "Vínculo excede tempo da tarefa", "#ffd43b")
        else:
            self._limpar_msg_vinculo(vinculo)

    @staticmethod
    def _mostrar_msg_vinculo(vinculo, mensagem, cor):
        vinculo["msg_label"].config(text=mensagem, fg=cor)
        vinculo["msg_label"].pack(anchor="w", padx=3, pady=(0, 4))

    @staticmethod
    def _limpar_msg_vinculo(vinculo):
        vinculo["msg_label"].config(text="")
        vinculo["msg_label"].pack_forget()

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
        self._update_resources_visibility()
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
        row = tk.Frame(self.rows_container, bg=theme.SIDEBAR_BG)
        row.pack(fill="x", pady=5)
        self._configure_row_columns(row)

        # o número exibido é sempre a posição na lista (1-based) — nunca um
        # contador à parte, senão ele diverge depois de remover uma linha
        # (ex: tira a 2, adiciona outra, e ela apareceria como "4" em vez de "3")
        id_label = tk.Label(
            row, text=str(len(self.task_rows) + 1), bg=theme.SIDEBAR_BG, fg=theme.TEXT_MUTED,
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

    def _mostrar_erro_tarefas(self, mensagem):
        self.tasks_error_label.config(text=mensagem)
        self.tasks_error_label.pack_configure(pady=(0, 14))

    def _limpar_erro_tarefas(self):
        self.tasks_error_label.config(text="")
        self.tasks_error_label.pack_configure(pady=0)

    def _limpar_tarefas_invalidas(self):
        """Remove da tela as tarefas com duração 0 (nunca preenchidas) e garante
        que sobrem pelo menos 2 linhas visíveis (só de exibição — as que forem
        adicionadas aqui têm duração 0 e não são enviadas pro algoritmo)."""
        invalidas = [row for row in self.task_rows if row["entries"][1].get_value() <= 0]
        for row in invalidas:
            row["frame"].destroy()
            self.task_rows.remove(row)
        self._renumber_rows()

        while len(self.task_rows) < 2:
            self._add_task_row()

    # --------------------------------------------------------- monta objetos
    def _build_tarefas(self) -> list[Tarefa]:
        tarefas = []
        proximo_id = 1
        for row in self.task_rows:
            chegada_entry, duracao_entry, prioridade_entry = row["entries"]
            duracao = duracao_entry.get_value()
            if duracao <= 0:
                continue  # linha só de exibição (preenchimento), não entra na simulação
            tarefas.append(Tarefa(
                id=proximo_id,
                chegada=chegada_entry.get_value(),
                tp=duracao,
                prioridade=prioridade_entry.get_value(),
            ))
            proximo_id += 1
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

    # ---------------------------------------------------------- salvar/abrir
    def _build_cenario_dict(self) -> dict:
        """Todos os inputs do formulário, inclusive os campos ocultos/travados
        no momento (quantum, protocolo de correção, prioridade) — só assim dá
        pra trocar de algoritmo depois de recarregar sem perder nada."""
        return {
            "algoritmo": self.scheduler_dropdown.get(),
            "ctx_time": self.ctx_entry.get_value(),
            "quantum": self.quantum_entry.get_value(),
            "protocolo_correcao": self.correction_dropdown.get(),
            "tarefas": [
                {
                    "chegada": row["entries"][0].get_value(),
                    "duracao": row["entries"][1].get_value(),
                    "prioridade": row["entries"][2].get_value(),
                }
                for row in self.task_rows
            ],
        }

    def _on_save_click(self):
        caminho = filedialog.asksaveasfilename(
            title="Salvar cenário",
            defaultextension=".json",
            filetypes=[("Cenário (JSON)", "*.json")],
        )
        if not caminho:
            return  # usuário cancelou o diálogo

        cenario = self._build_cenario_dict()
        with open(caminho, "w", encoding="utf-8") as arquivo:
            json.dump(cenario, arquivo, indent=2, ensure_ascii=False)

    def _on_open_scenario_click(self):
        caminho = filedialog.askopenfilename(
            title="Abrir cenário",
            filetypes=[("Cenário (JSON)", "*.json")],
        )
        if not caminho:
            return  # usuário cancelou o diálogo

        try:
            with open(caminho, encoding="utf-8") as arquivo:
                cenario = json.load(arquivo)
        except (OSError, json.JSONDecodeError):
            self._mostrar_erro_tarefas("Esse arquivo não é um cenário válido.")
            return

        if not validar_cenario(cenario):
            self._mostrar_erro_tarefas("Esse arquivo não é um cenário válido.")
            return

        self.carregar_cenario(cenario)

    def carregar_cenario(self, cenario: dict):
        """Preenche a tela inteira a partir de um dict já validado (validar_cenario).
        Chame ANTES de mostrar essa tela — a ordem importa: o algoritmo primeiro,
        pra especificações/trava de prioridade já nascerem certas nas tarefas."""
        self.scheduler_dropdown.set_value(cenario["algoritmo"])
        self.ctx_entry.set_value(cenario["ctx_time"])
        self.quantum_entry.set_value(cenario["quantum"])
        self.correction_dropdown.set_value(cenario["protocolo_correcao"])

        for row in list(self.task_rows):
            row["frame"].destroy()
        self.task_rows.clear()

        tarefas = cenario["tarefas"] or [{}, {}]
        for dado in tarefas:
            self._add_task_row()
            chegada_entry, duracao_entry, prioridade_entry = self.task_rows[-1]["entries"]
            chegada_entry.set_value(dado.get("chegada", 0))
            duracao_entry.set_value(dado.get("duracao", 0))
            prioridade_entry.set_value(dado.get("prioridade", 1))

        self._limpar_erro_specs()
        self._limpar_erro_tarefas()
        self._draw_empty_chart()

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

    @staticmethod
    def _calcular_esperas(tr):
        """Espera nunca é um Periodo de verdade (nenhum algoritmo registra) — é
        derivada aqui: os buracos entre a chegada e o que os períodos já cobrem.
        Não conta o tempo depois do último período (aí a tarefa já terminou)."""
        periodos_ordenados = sorted(tr.periodos, key=lambda p: p.inicio)
        esperas = []
        posicao = tr.tarefa.chegada
        for periodo in periodos_ordenados:
            if periodo.inicio > posicao:
                esperas.append((posicao, periodo.inicio))
            posicao = max(posicao, periodo.fim)
        return esperas

    def _desenhar_resultado(self, resultado: ResultadoSimulacao):
        self.ax.clear()
        self._style_axes()

        tarefas_resultado = sorted(resultado.tarefas.values(), key=lambda tr: tr.tarefa.id)
        tempo_max = max(periodo.fim for tr in tarefas_resultado for periodo in tr.periodos)

        for tr in tarefas_resultado:
            for inicio, fim in self._calcular_esperas(tr):
                self.ax.barh(
                    tr.tarefa.id, fim - inicio, left=inicio,
                    fill=False, edgecolor=CHART_ESPERA, linewidth=1.2, height=0.55,
                )
            for periodo in tr.periodos:
                cor = CHART_EXECUCAO if periodo.tipo == TipoPeriodo.EXECUCAO else CHART_TROCA_CONTEXTO
                borda = theme.PURPLE_DARK
                self.ax.barh(
                    tr.tarefa.id, periodo.fim - periodo.inicio, left=periodo.inicio,
                    color=cor, edgecolor=borda, linewidth=1.2, height=0.55,
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
