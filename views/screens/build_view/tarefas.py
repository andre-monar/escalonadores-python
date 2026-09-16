import tkinter as tk

from models.tarefa import Tarefa
from views import theme
from views.components.placeholder_numeric_entry import PlaceholderNumericEntry
from views.components.rounded_button import RoundedButton
from views.components.trash_icon_button import TrashIconButton
from views.screens.build_view.constants import ALGORITMOS_COM_PRIORIDADE, SIDEBAR_PAD

COLUMN_LABELS = ["ID", "Chegada", "", "Duração", "", "Prioridade", "", ""]
# (col_entry, col_unidade, unidade, placeholder/mínimo)
TASK_FIELDS = [(1, 2, "s", 0), (3, 4, "s", 0), (5, 6, "", 1)]


class TarefasMixin:
    def _build_tasks_section(self, sidebar, content_width):
        self._tarefas_titulo = tk.Label(
            sidebar, text="Tarefas", bg=theme.SIDEBAR_BG, fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 14, "bold"),
        )
        self._tarefas_titulo.pack(anchor="w", padx=SIDEBAR_PAD, pady=(0, 10))

        RoundedButton(
            sidebar, "Abrir cenário",
            command=self._on_open_scenario_click,
            width=content_width, height=48, radius=10,
            bg=theme.SURFACE, hover=theme.SURFACE_HOVER,
            fg=theme.TEXT, outline=theme.BORDER,
            font=(theme.FONT_FAMILY, 11, "bold"),
        ).pack(padx=SIDEBAR_PAD, pady=(0, 10))

        self.tasks_error_label = tk.Label(
            sidebar, text="", bg=theme.SIDEBAR_BG, fg=theme.DANGER,
            font=(theme.FONT_FAMILY, 10), anchor="w", justify="left",
            wraplength=content_width,
        )
        self.tasks_error_label.pack(anchor="w", padx=SIDEBAR_PAD, pady=0)

        header = tk.Frame(sidebar, bg=theme.SIDEBAR_BG)
        header.pack(fill="x", padx=SIDEBAR_PAD)
        self._configure_row_columns(header)
        for col, text in enumerate(COLUMN_LABELS):
            tk.Label(
                header, text=text, bg=theme.SIDEBAR_BG, fg=theme.TEXT_MUTED,
                font=(theme.FONT_FAMILY, 9, "bold"), anchor="w",
            ).grid(row=0, column=col, sticky="ew", padx=4)

        self.rows_container = tk.Frame(sidebar, bg=theme.SIDEBAR_BG)
        self.rows_container.pack(fill="x", padx=SIDEBAR_PAD, pady=(6, 14))

        RoundedButton(
            sidebar, "+  Adicionar tarefa",
            command=self._add_task_row,
            width=content_width, height=48, radius=10,
            bg=theme.SURFACE, hover=theme.SURFACE_HOVER,
            fg=theme.TEXT, outline=theme.BORDER,
            font=(theme.FONT_FAMILY, 11, "bold"),
        ).pack(padx=SIDEBAR_PAD, pady=(0, 16))

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

        remove_btn = TrashIconButton(row, command=lambda: self._remove_task_row(entry_data), size=22)
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

    def _update_priority_lock(self):
        travar = self.scheduler_dropdown.get() not in ALGORITMOS_COM_PRIORIDADE
        for row in self.task_rows:
            row["prioridade_entry"].set_locked(travar)

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
