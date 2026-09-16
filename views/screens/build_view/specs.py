import tkinter as tk

from views import theme
from views.components.dropdown import Dropdown
from views.components.placeholder_numeric_entry import PlaceholderNumericEntry
from views.screens.build_view.constants import (
    ALGO_PRIOP,
    ALGO_ROUND_ROBIN,
    CORRECTION_DEFAULT,
    CORRECTION_OPTIONS,
    SIDEBAR_PAD,
)


class SpecsMixin:
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

        self.specs_error_label = tk.Label(
            sidebar, text="", bg=theme.SIDEBAR_BG, fg=theme.DANGER,
            font=(theme.FONT_FAMILY, 10), anchor="w", justify="left",
            wraplength=content_width,
        )
        # empacotado já na posição certa (entre Especificações e Recursos/Tarefas),
        # com padding zerado — _mostrar_erro_specs/_limpar_erro_specs só ajustam o
        # padding depois (pack_configure preserva a posição; um pack() novo não)
        self.specs_error_label.pack(anchor="w", padx=SIDEBAR_PAD, pady=0)

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
