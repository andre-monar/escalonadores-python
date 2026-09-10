import tkinter as tk

from views import theme

class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command=None, width=180, height=44, radius=None,
                 bg=None, hover=None, fg=None, font=None, outline=None, parent_bg=None):
        self.radius = radius if radius is not None else height // 2
        self.width = width
        self.height = height
        self.bg_color = bg or theme.PURPLE
        self.hover_color = hover or theme.PURPLE_HOVER
        self.fg_color = fg or theme.TEXT
        self.text = text
        self.font = font or (theme.FONT_FAMILY, 11, "bold")
        self.outline = outline
        self.command = command
        self.enabled = True

        bg_canvas = parent_bg or parent.cget("bg")
        super().__init__(parent, width=width, height=height, bg=bg_canvas,
                          highlightthickness=0, bd=0)

        self._render(self.bg_color)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        if event.width == self.width and event.height == self.height:
            return
        self.width = event.width
        self.height = event.height
        self._render(self.bg_color if self.enabled else theme.BORDER)

    def _round_rect(self, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
            x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
            x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def _render(self, fill_color):
        self.delete("all")
        outline_color = self.outline or fill_color
        self._round_rect(1, 1, self.width - 1, self.height - 1, self.radius,
                          fill=fill_color, outline=outline_color, width=1.4)
        self.create_text(self.width / 2, self.height / 2, text=self.text,
                          fill=self.fg_color, font=self.font)

    def _on_enter(self, _event):
        if not self.enabled:
            return
        self._render(self.hover_color)
        self.config(cursor="hand2")

    def _on_leave(self, _event):
        if not self.enabled:
            return
        self._render(self.bg_color)

    def _on_click(self, _event):
        if self.enabled and self.command:
            self.command()

    def set_enabled(self, enabled):
        self.enabled = enabled
        self._render(self.bg_color if enabled else theme.BORDER)
        self.config(cursor="arrow" if not enabled else "hand2")