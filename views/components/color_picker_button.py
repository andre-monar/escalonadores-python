import tkinter as tk

from views import theme


class ColorPickerButton(tk.Frame):
    """Quadradinho que mostra a cor atual e abre uma grade de cores fixas ao
    clicar (não é o color-chooser nativo do SO — é uma paleta curta, no mesmo
    estilo do resto da tela). Mesmo esqueleto de popup do Dropdown."""

    def __init__(self, parent, cores, initial=None, size=32, colunas=5,
                 command=None, parent_bg=None):
        bg = parent_bg or parent.cget("bg")
        super().__init__(parent, bg=bg)

        self.cores = cores
        self.colunas = colunas
        self.command = command
        self.size = size
        self.value = initial if initial in cores else cores[0]
        self._popup = None
        self._outside_click_binding = None
        self._unmap_binding = None

        self.swatch = tk.Canvas(self, width=size, height=size, bg=bg,
                                 highlightthickness=0, bd=0, cursor="hand2")
        self.swatch.pack()
        self._render_swatch()
        self.swatch.bind("<Button-1>", self._toggle_popup)

    def _render_swatch(self):
        c = self.swatch
        c.delete("all")
        c.create_rectangle(2, 2, self.size - 2, self.size - 2,
                            fill=self.value, outline=theme.BORDER, width=1.4)

    def get(self):
        return self.value

    def set_value(self, valor):
        if valor not in self.cores:
            return
        self.value = valor
        self._render_swatch()

    def _toggle_popup(self, _event=None):
        if self._popup is not None:
            self._close_popup()
        else:
            self._open_popup()

    def _open_popup(self):
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.size + 4

        popup = tk.Toplevel(self)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(bg=theme.BORDER)

        inner = tk.Frame(popup, bg=theme.CARD_BG)
        inner.pack(padx=1, pady=1)

        swatch_size = 26
        for indice, cor in enumerate(self.cores):
            linha, coluna = divmod(indice, self.colunas)
            swatch = tk.Canvas(inner, width=swatch_size, height=swatch_size,
                                bg=theme.CARD_BG, highlightthickness=0, bd=0, cursor="hand2")
            swatch.create_rectangle(2, 2, swatch_size - 2, swatch_size - 2,
                                     fill=cor, outline=theme.BORDER, width=1.4)
            swatch.grid(row=linha, column=coluna, padx=4, pady=4)
            swatch.bind("<Button-1>", lambda _e, c=cor: self._select(c))

        popup.update_idletasks()
        popup.geometry(f"+{x}+{y}")

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
            if node in (self._popup, self.swatch):
                return
            node = getattr(node, "master", None)
        self._close_popup()

    def _on_root_unmap(self, _event):
        self._close_popup()

    def _select(self, cor):
        self.value = cor
        self._close_popup()
        self._render_swatch()
        if self.command:
            self.command(cor)

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
