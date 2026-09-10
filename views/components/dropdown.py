import tkinter as tk

from views import theme


class Dropdown(tk.Frame):
    def __init__(self, parent, options, initial=None, width=300, height=48,
                 command=None, parent_bg=None, desabilitados=None, options_provider=None,
                 placeholder=None):
        bg = parent_bg or parent.cget("bg")
        super().__init__(parent, bg=bg)

        # cada opção é (valor, rótulo) — `get()` devolve o valor, a tela mostra o rótulo.
        # aceita também uma lista simples de strings, onde valor == rótulo.
        self.options = [o if isinstance(o, tuple) else (o, o) for o in options]
        self.desabilitados = desabilitados or set()
        self.command = command
        self.width = width
        self.height = height
        # se informado, é chamado toda vez que o popup abre — pra listas que
        # mudam depois de criado o dropdown (ex: "tarefas registradas agora")
        self.options_provider = options_provider
        # com placeholder definido, nenhuma opção é selecionada por padrão —
        # sem ele, mantém o comportamento antigo (cai na primeira opção)
        self.placeholder = placeholder

        valores = [valor for valor, _ in self.options]
        if initial is not None and initial in valores:
            self.value = initial
        elif self.placeholder is not None:
            self.value = None
        else:
            self.value = valores[0] if valores else ""
        self._popup = None
        self._outside_click_binding = None
        self._unmap_binding = None

        self.field = tk.Canvas(self, width=width, height=height, bg=bg,
                                highlightthickness=0, bd=0, cursor="hand2")
        self.field.pack()

        self._render_field()
        self.field.bind("<Button-1>", self._toggle_popup)

    def _round_rect(self, canvas, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
            x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
            x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
        ]
        return canvas.create_polygon(points, smooth=True, **kwargs)

    def _render_field(self, open_state=False):
        c = self.field
        c.delete("all")
        fill = theme.SURFACE_HOVER if open_state else theme.SURFACE
        outline = theme.PURPLE if open_state else theme.BORDER
        self._round_rect(c, 1, 1, self.width - 1, self.height - 1, 10,
                          fill=fill, outline=outline, width=1.4)
        c.create_text(16, self.height / 2, text=self._rotulo_atual(), anchor="w",
                       fill=theme.TEXT, font=(theme.FONT_FAMILY, 11))

        cx, cy = self.width - 24, self.height / 2
        if open_state:
            c.create_polygon(cx - 6, cy + 3, cx + 6, cy + 3, cx, cy - 5,
                              fill=theme.TEXT_MUTED, outline="")
        else:
            c.create_polygon(cx - 6, cy - 3, cx + 6, cy - 3, cx, cy + 5,
                              fill=theme.TEXT_MUTED, outline="")

    def _rotulo_atual(self):
        if self.value is None:
            return self.placeholder or ""
        for valor, rotulo in self.options:
            if valor == self.value:
                return rotulo
        return self.value

    def set_options(self, options):
        """Atualiza a lista de opções (ex: tarefas registradas mudaram). Se o
        valor atual não existir mais na lista nova, volta pro placeholder (ou
        pra primeira opção, se não tiver placeholder) em vez de manter uma
        referência inválida."""
        self.options = [o if isinstance(o, tuple) else (o, o) for o in options]
        valores = [v for v, _ in self.options]
        if self.value not in valores:
            self.value = None if self.placeholder is not None else (valores[0] if valores else "")

    def _toggle_popup(self, _event=None):
        if self._popup is not None:
            self._close_popup()
        else:
            self._open_popup()

    def _open_popup(self):
        if self.options_provider is not None:
            self.set_options(self.options_provider())
        self._render_field(open_state=True)

        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.height + 4

        popup = tk.Toplevel(self)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(bg=theme.BORDER)

        inner = tk.Frame(popup, bg=theme.CARD_BG)
        inner.pack(padx=1, pady=1, fill="both", expand=True)

        for valor, rotulo in self.options:
            desabilitado = valor in self.desabilitados
            row = tk.Label(
                inner, text=rotulo, bg=theme.CARD_BG,
                fg=theme.TEXT_MUTED if desabilitado else theme.TEXT, anchor="w",
                font=(theme.FONT_FAMILY, 11), padx=16, pady=10,
                cursor="arrow" if desabilitado else "hand2",
            )
            row.pack(fill="x")
            if not desabilitado:
                row.bind("<Enter>", lambda e, r=row: r.config(bg=theme.PURPLE))
                row.bind("<Leave>", lambda e, r=row: r.config(bg=theme.CARD_BG))
                row.bind("<Button-1>", lambda e, v=valor: self._select(v))

        popup.update_idletasks()
        popup_width = max(self.width, popup.winfo_reqwidth())
        popup.geometry(f"{popup_width}x{popup.winfo_reqheight()}+{x}+{y}")

        self._popup = popup
        root = self.winfo_toplevel()
        self._outside_click_binding = root.bind("<Button-1>", self._on_global_click, add="+")
        self._unmap_binding = root.bind("<Unmap>", self._on_root_unmap, add="+")

    def _on_global_click(self, event):
        if self._popup is None:
            return
        widget = self.winfo_containing(event.x_root, event.y_root)
        node = widget
        while node is not None:
            if node in (self._popup, self.field):
                return
            node = getattr(node, "master", None)
        self._close_popup()

    def _on_root_unmap(self, _event):
        self._close_popup()

    def _select(self, option):
        self.value = option
        self._close_popup()
        self._render_field()
        if self.command:
            self.command(option)

    def _close_popup(self):
        if self._popup is not None:
            self._popup.destroy()
            self._popup = None
        if self._outside_click_binding is not None:
            self.winfo_toplevel().unbind("<Button-1>", self._outside_click_binding)
            self._outside_click_binding = None
        if self._unmap_binding is not None:
            self.winfo_toplevel().unbind("<Unmap>", self._unmap_binding)
            self._unmap_binding = None
        self._render_field()

    def get(self):
        return self.value

    def set_value(self, valor):
        """Define o valor programaticamente (ex: ao carregar um cenário salvo) —
        dispara o mesmo callback de quando o usuário seleciona na lista. Se
        `valor` não for uma opção reconhecida, ignora e mantém o que já tinha."""
        if valor not in {v for v, _ in self.options}:
            return
        self._select(valor)