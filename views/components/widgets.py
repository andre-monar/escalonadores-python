import tkinter as tk

from views import theme


class RoundedButton(tk.Canvas):
    """Botão com cantos arredondados desenhado em Canvas (tkinter não tem isso nativo)."""

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


class TrashIcon(tk.Canvas):
    """Ícone de lixeira desenhado em Canvas (emoji fica colorido demais e ignora `fg`)."""

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


class ScrollableFrame(tk.Frame):
    """Área com scroll vertical. O conteúdo real vai dentro de `self.inner`."""

    def __init__(self, parent, bg=None):
        bg = bg or theme.SIDEBAR_BG
        super().__init__(parent, bg=bg)

        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=bg)

        self.inner.bind("<Configure>", self._on_inner_configure)
        self._window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)

    def _on_inner_configure(self, _event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self._window, width=event.width)

    def _bind_mousewheel(self, _event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, _event):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


def draw_horizontal_gradient(canvas, x1, y1, x2, y2, color1, color2, steps=80):
    r1, g1, b1 = canvas.winfo_rgb(color1)
    r2, g2, b2 = canvas.winfo_rgb(color2)
    width = x2 - x1
    for i in range(steps):
        nr = int(r1 + (r2 - r1) * i / steps) >> 8
        ng = int(g1 + (g2 - g1) * i / steps) >> 8
        nb = int(b1 + (b2 - b1) * i / steps) >> 8
        color = f"#{nr:02x}{ng:02x}{nb:02x}"
        seg_x1 = x1 + width * i / steps
        seg_x2 = x1 + width * (i + 1) / steps + 1
        canvas.create_rectangle(seg_x1, y1, seg_x2, y2, fill=color, outline=color)


def draw_gradient_pill(canvas, x1, y1, x2, y2, color1, color2, steps=80):
    """Retângulo em formato de cápsula (pontas arredondadas) com gradiente horizontal."""
    radius = (y2 - y1) / 2
    canvas.create_oval(x1, y1, x1 + 2 * radius, y2, fill=color1, outline=color1)
    canvas.create_oval(x2 - 2 * radius, y1, x2, y2, fill=color2, outline=color2)
    draw_horizontal_gradient(canvas, x1 + radius, y1, x2 - radius, y2, color1, color2, steps)
