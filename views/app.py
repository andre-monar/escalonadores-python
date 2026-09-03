import tkinter as tk

from views import theme
from views.screens.build_view import BuildView
from views.screens.home_view import HomeView


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simulador de Escalonamento")
        self.configure(bg=theme.BG)
        self.geometry("1280x800")
        self.minsize(1024, 680)
        self._centralizar(1280, 800)

        container = tk.Frame(self, bg=theme.BG)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for view_class in (HomeView, BuildView):
            frame = view_class(container, self)
            self.frames[view_class.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("HomeView")

    def show_frame(self, name):
        self.frames[name].tkraise()

    def _centralizar(self, largura, altura):
        largura_tela = self.winfo_screenwidth()
        altura_tela = self.winfo_screenheight()
        pos_x = (largura_tela // 2) - (largura // 2)
        pos_y = (altura_tela // 2) - (altura // 2)
        self.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")
