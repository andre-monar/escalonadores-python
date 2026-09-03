import tkinter as tk

from views import theme
from views.components.widgets import RoundedButton


class HomeView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=theme.BG)
        self.controller = controller

        self._build_hero()
        self._build_actions()
        self._build_footer()

    def _build_hero(self):
        self.hero = tk.Canvas(self, bg=theme.BG, highlightthickness=0, height=170)
        self.hero.pack(fill="x", pady=(140, 0))
        self.hero.bind("<Configure>", self._draw_hero)

    def _draw_hero(self, event=None):
        canvas = self.hero
        canvas.delete("all")
        width = canvas.winfo_width()
        if width <= 1:
            width = self.winfo_width() or 1280
        cx = width / 2
        title_cy = 60

        canvas.create_text(
            cx, title_cy, text="Simulador de Escalonamento",
            fill=theme.TEXT, font=(theme.FONT_FAMILY, 28, "bold"),
        )
        canvas.create_text(
            cx, title_cy + 62, text="Sistemas Operacionais — simule e compare algoritmos de escalonamento de tarefas",
            fill=theme.TEXT_MUTED, font=(theme.FONT_FAMILY, 12),
        )

    def _build_actions(self):
        actions = tk.Frame(self, bg=theme.BG)
        actions.pack(pady=40)

        RoundedButton(
            actions, "Criar novo cenário",
            command=lambda: self.controller.show_frame("BuildView"),
            width=230, height=52, bg=theme.PURPLE, hover=theme.PURPLE_HOVER,
        ).pack(side="left", padx=12)

        RoundedButton(
            actions, "Abrir cenário",
            command=self._open_scenario_placeholder,
            width=200, height=52, bg=theme.BG, hover=theme.CARD_BG,
            fg=theme.TEXT, outline=theme.BORDER,
        ).pack(side="left", padx=12)

    def _open_scenario_placeholder(self):
        pass

    def _build_footer(self):
        tk.Label(
            self, text="Projeto prático — Sistemas Operacionais",
            bg=theme.BG, fg=theme.TEXT_MUTED, font=(theme.FONT_FAMILY, 9),
        ).pack(side="bottom", pady=18)
