import tkinter as tk

from views import theme


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
