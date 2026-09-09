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
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        # redesenha do tamanho novo quando o gerenciador de geometria (grid
        # com sticky="ew"/weight, por exemplo) estica o botão além do
        # width/height pedidos na criação — sem isso o retângulo desenhado
        # fica "flutuando" pequeno dentro de um canvas maior.
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


class Dropdown(tk.Frame):
    """Seletor estilo combobox, desenhado do zero pra bater com o tema escuro/roxo
    (o ttk.Combobox nativo não dá pra estilizar direito, principalmente a lista)."""

    def __init__(self, parent, options, initial=None, width=300, height=48,
                 command=None, parent_bg=None, desabilitados=None):
        bg = parent_bg or parent.cget("bg")
        super().__init__(parent, bg=bg)

        # cada opção é (valor, rótulo) — `get()` devolve o valor, a tela mostra o rótulo.
        # aceita também uma lista simples de strings, onde valor == rótulo.
        self.options = [o if isinstance(o, tuple) else (o, o) for o in options]
        self.desabilitados = desabilitados or set()
        self.command = command
        self.width = width
        self.height = height

        valores = [valor for valor, _ in self.options]
        self.value = initial if initial in valores else (valores[0] if valores else "")
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
        for valor, rotulo in self.options:
            if valor == self.value:
                return rotulo
        return self.value

    def _toggle_popup(self, _event=None):
        if self._popup is not None:
            self._close_popup()
        else:
            self._open_popup()

    def _open_popup(self):
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


class PlaceholderNumericEntry(tk.Entry):
    """Entry numérico com placeholder visual: mostra um valor inicial em cinza (que
    também é o mínimo aceito) até o usuário digitar algo válido por cima. Bloqueia
    negativos e não-dígitos na digitação; valores abaixo do placeholder ao sair do
    campo fazem ele voltar a mostrar o placeholder.

    Aceita decimais com vírgula (padrão brasileiro) — "." digitado vira "," na hora.
    Só permite uma vírgula por número, e completa com "0" o lado que faltar (ex: "3,"
    vira "3,0") quando o campo perde o foco.
    """

    def __init__(self, parent, placeholder, width=8):
        self.placeholder = placeholder
        self._is_placeholder = True

        super().__init__(
            parent, width=width, bg=theme.CARD_BG, fg=theme.TEXT_MUTED,
            insertbackground=theme.TEXT, relief="flat", justify="center",
            font=(theme.FONT_FAMILY, 11),
            highlightthickness=1, highlightbackground=theme.BORDER,
            highlightcolor=theme.PURPLE,
            disabledbackground=theme.BORDER, disabledforeground=theme.TEXT_MUTED,
        )
        vcmd = (self.register(self._validate_keystroke), "%P")
        self.config(validate="key", validatecommand=vcmd)

        self.insert(0, str(placeholder))
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<KeyPress-period>", self._trocar_ponto_por_virgula)
        self.bind("<KeyPress-KP_Decimal>", self._trocar_ponto_por_virgula)

    @staticmethod
    def _validate_keystroke(proposed):
        if proposed == "":
            return True
        if proposed.count(",") > 1:
            return False
        return all(ch.isdigit() or ch == "," for ch in proposed)

    def _trocar_ponto_por_virgula(self, _event):
        self.insert(self.index("insert"), ",")
        return "break"

    def _on_focus_in(self, _event):
        if self._is_placeholder:
            self.delete(0, "end")
            self.config(fg=theme.TEXT)
            self._is_placeholder = False

    def _on_focus_out(self, _event):
        texto = self.get().strip()
        if texto == "":
            self._show_placeholder()
            return

        texto = self._normalizar(texto)
        if texto != self.get():
            self.delete(0, "end")
            self.insert(0, texto)

        if self._para_float(texto) < self.placeholder:
            self._show_placeholder()
        else:
            self.config(fg=theme.TEXT)
            self._is_placeholder = False

    @staticmethod
    def _normalizar(texto):
        """Completa com '0' o lado que faltar de uma vírgula (ex: '3,' -> '3,0')."""
        if "," not in texto:
            return texto
        antes, depois = texto.split(",", 1)
        return f"{antes or '0'},{depois or '0'}"

    @staticmethod
    def _para_float(texto):
        return float(texto.replace(",", "."))

    def _show_placeholder(self):
        self.delete(0, "end")
        self.insert(0, str(self.placeholder))
        self.config(fg=theme.TEXT_MUTED)
        self._is_placeholder = True

    def get_value(self):
        """Valor efetivo: o que o usuário digitou (int se for inteiro, float se tiver
        casas decimais), ou o placeholder se ele nunca digitou nada."""
        texto = self.get().strip()
        if self._is_placeholder or texto == "":
            return self.placeholder
        valor = self._para_float(texto)
        return int(valor) if valor.is_integer() else valor

    def set_locked(self, locked: bool):
        """Trava o campo (cinza, não clicável) mantendo o valor guardado por baixo."""
        if locked:
            self.config(state="disabled")
        else:
            self.config(state="normal", fg=theme.TEXT_MUTED if self._is_placeholder else theme.TEXT)

    def set_value(self, valor):
        """Define o valor programaticamente (ex: ao carregar um cenário salvo).
        Passa pela mesma checagem de mínimo do placeholder — um valor inválido
        simplesmente volta a mostrar o placeholder, igual digitação manual."""
        estava_travado = self.cget("state") == "disabled"
        if estava_travado:
            self.config(state="normal")

        self.delete(0, "end")
        self.insert(0, str(valor).replace(".", ","))
        self._is_placeholder = False
        self._on_focus_out(None)

        if estava_travado:
            self.config(state="disabled")


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
