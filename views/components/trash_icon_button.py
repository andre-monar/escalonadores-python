import tkinter as tk

from views import theme


class TrashIconButton(tk.Canvas):
    def __init__(self, parent, command=None, size=22, color=None, hover_color=None, parent_bg=None):
        self.command = command
        self.size = size
        self.color = color or theme.TEXT_MUTED
        self.hover_color = hover_color or theme.DANGER

        bg_canvas = parent_bg or parent.cget("bg")
        super().__init__(parent, width=size, height=size, bg=bg_canvas,
                          highlightthickness=0, bd=0)

        self._render(self.color)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _render(self, color):
        self.delete("all")
        s = self.size
        pad = s * 0.16

        self.create_line(s * 0.4, s * 0.18, s * 0.6, s * 0.18, fill=color, width=1.6, capstyle="round")
        self.create_line(pad, s * 0.3, s - pad, s * 0.3, fill=color, width=1.8, capstyle="round")
        self.create_polygon(
            pad * 1.4, s * 0.32, s - pad * 1.4, s * 0.32, s - pad * 1.7, s - pad * 0.9, pad * 1.7, s - pad * 0.9,
            outline=color, fill="", width=1.8, joinstyle="round",
        )
        self.create_line(s * 0.42, s * 0.44, s * 0.42, s * 0.78, fill=color, width=1.4)
        self.create_line(s * 0.58, s * 0.44, s * 0.58, s * 0.78, fill=color, width=1.4)

    def _on_enter(self, _event):
        self._render(self.hover_color)
        self.config(cursor="hand2")

    def _on_leave(self, _event):
        self._render(self.color)

    def _on_click(self, _event):
        if self.command:
            self.command()
