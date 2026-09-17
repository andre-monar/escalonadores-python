import tkinter as tk

from views import theme
from views.components.color_picker_button import ColorPickerButton
from views.components.dropdown import Dropdown
from views.components.placeholder_numeric_entry import PlaceholderNumericEntry
from views.components.rounded_button import RoundedButton
from views.components.trash_icon_button import TrashIconButton
from views.screens.build_view.constants import ALGO_PRIOP, SIDEBAR_PAD

RESOURCE_COLUMN_LABELS = ["ID", "Cor", "Configurar", ""]
RESOURCE_COLORS = [
    "#ff6b6b", "#ffa94d", "#ffd43b", "#69db7c", "#38d9a9",
    "#4dabf7", "#748ffc", "#9775fa", "#f783ac", "#ced4da",
]

VINCULO_COLUMN_LABELS = [
    "Tarefa", "T.Ini\n(Tarefa)", "T.Ini\n(Recurso)", "T.Fim\n(Recurso)", "T.Fim\n(Tarefa)", "",
]


class RecursosMixin:
    # a seção inteira (título, tabela, botão) só aparece pro PRIOp — é onde
    # entram os recursos compartilhados pra seção crítica (R5-R7).
    def _build_resources(self, sidebar, content_width):
        self.resources_section = tk.Frame(sidebar, bg=theme.SIDEBAR_BG)

        tk.Label(
            self.resources_section, text="Recursos", bg=theme.SIDEBAR_BG, fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 14, "bold"),
        ).pack(anchor="w", padx=SIDEBAR_PAD, pady=(0, 10))

        header = tk.Frame(self.resources_section, bg=theme.SIDEBAR_BG)
        header.pack(fill="x", padx=SIDEBAR_PAD)
        self._configure_resource_row_columns(header)
        for col, text in enumerate(RESOURCE_COLUMN_LABELS):
            tk.Label(
                header, text=text, bg=theme.SIDEBAR_BG, fg=theme.TEXT_MUTED,
                font=(theme.FONT_FAMILY, 9, "bold"), anchor="w",
            ).grid(row=0, column=col, sticky="ew", padx=4)

        self.resource_rows_container = tk.Frame(self.resources_section, bg=theme.SIDEBAR_BG)
        self.resource_rows_container.pack(fill="x", padx=SIDEBAR_PAD, pady=(6, 14))

        RoundedButton(
            self.resources_section, "+  Adicionar recurso",
            command=self._add_resource_row,
            width=content_width, height=48, radius=10,
            bg=theme.SURFACE, hover=theme.SURFACE_HOVER,
            fg=theme.TEXT, outline=theme.BORDER,
            font=(theme.FONT_FAMILY, 11, "bold"),
        ).pack(padx=SIDEBAR_PAD, pady=(0, 16))

        self._update_resources_visibility()

    def _update_resources_visibility(self):
        if self.scheduler_dropdown.get() == ALGO_PRIOP:
            self.resources_section.pack(anchor="w", fill="x", before=self._tarefas_titulo)
        else:
            self.resources_section.pack_forget()

    @staticmethod
    def _configure_resource_row_columns(row):
        row.grid_columnconfigure(0, weight=0, minsize=26)   # ID (mesmo tamanho de Tarefas)
        row.grid_columnconfigure(1, weight=0, minsize=40)    # Cor
        row.grid_columnconfigure(2, weight=1)                # Configurar
        row.grid_columnconfigure(3, weight=0, minsize=34)    # lixeira

    def _add_resource_row(self):
        row = tk.Frame(self.resource_rows_container, bg=theme.SIDEBAR_BG)
        row.pack(fill="x", pady=5)
        self._configure_resource_row_columns(row)

        novo_id = len(self.resource_rows) + 1
        id_label = tk.Label(
            row, text=str(novo_id), bg=theme.SIDEBAR_BG, fg=theme.TEXT_MUTED,
            font=(theme.FONT_FAMILY, 10), anchor="w",
        )
        id_label.grid(row=0, column=0, sticky="ew", padx=4)

        # cor inicial roda pela paleta a cada recurso novo (id 1 -> 1ª cor,
        # id 2 -> 2ª cor, ...), voltando pra primeira depois de esgotar todas
        cor_inicial = RESOURCE_COLORS[(novo_id - 1) % len(RESOURCE_COLORS)]
        cor_picker = ColorPickerButton(row, RESOURCE_COLORS, initial=cor_inicial, size=28)
        cor_picker.grid(row=0, column=1, sticky="w", padx=4)

        entry_data = {
            "frame": row, "id_label": id_label, "cor_picker": cor_picker,
            "vinculos": [], "popup": None,
            "popup_click_binding": None, "popup_unmap_binding": None,
        }

        configurar_btn = RoundedButton(
            row, "Configurar",
            command=lambda: self._abrir_configurar_recurso(entry_data),
            width=110, height=36, radius=10,
            bg=theme.SURFACE, hover=theme.SURFACE_HOVER,
            fg=theme.TEXT, outline=theme.BORDER,
            font=(theme.FONT_FAMILY, 10, "bold"),
        )
        configurar_btn.grid(row=0, column=2, sticky="ew", padx=4)
        entry_data["configurar_btn"] = configurar_btn

        remove_btn = TrashIconButton(row, command=lambda: self._remove_resource_row(entry_data), size=22)
        remove_btn.grid(row=0, column=3, sticky="e", padx=4)

        self.resource_rows.append(entry_data)

    def _remove_resource_row(self, entry_data):
        self._fechar_configurar_recurso(entry_data)
        entry_data["frame"].destroy()
        self.resource_rows.remove(entry_data)
        self._renumber_resource_rows()

    def _renumber_resource_rows(self):
        for index, row in enumerate(self.resource_rows, start=1):
            row["id_label"].config(text=str(index))

    def _cores_dos_recursos(self) -> dict:
        """Cor configurada de cada recurso, por posição (mesma convenção de
        id usada em Recurso.id) — usado pelo gráfico pra colorir a faixa de
        posse."""
        return {
            indice: recurso["cor_picker"].get()
            for indice, recurso in enumerate(self.resource_rows, start=1)
        }

    # -------------------------------------------------- configurar recurso
    def _tarefas_disponiveis(self):
        """Opções pro dropdown "vincular tarefa" — sempre recalculado na hora
        de abrir, pra refletir as tarefas que existem AGORA (podem ter mudado
        desde a última vez que esse popup foi aberto)."""
        return [(indice, f"Tarefa {indice}") for indice in range(1, len(self.task_rows) + 1)]

    def _abrir_configurar_recurso(self, recurso):
        if recurso["popup"] is not None:
            self._fechar_configurar_recurso(recurso)
            return

        # snapshot só dos dados (não dos widgets) — pra "Cancelar" poder
        # voltar exatamente pro estado de antes de abrir, mesmo que a sessão
        # tenha adicionado/removido vínculo ou trocado a tarefa vinculada.
        recurso["_snapshot_vinculos"] = [
            {
                "tarefa_index": v["tarefa_index"],
                "t_inicial_recurso": v["t_inicial_recurso"],
                "t_final_recurso": v["t_final_recurso"],
            }
            for v in recurso["vinculos"]
        ]

        if not recurso["vinculos"]:
            recurso["vinculos"].append({"tarefa_index": None, "t_inicial_recurso": 0, "t_final_recurso": 0})

        botao = recurso["configurar_btn"]
        x = botao.winfo_rootx()
        y = botao.winfo_rooty() + botao.winfo_height() + 4

        popup = tk.Toplevel(self)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(bg=theme.BORDER)

        inner = tk.Frame(popup, bg=theme.CARD_BG)
        inner.pack(padx=1, pady=1)

        popup_state = {"recurso": recurso, "rows_container": None}

        header = tk.Frame(inner, bg=theme.CARD_BG)
        header.pack(padx=10, pady=(10, 4))
        self._configure_vinculo_row_columns(header)
        for col, texto in enumerate(VINCULO_COLUMN_LABELS):
            tk.Label(
                header, text=texto, bg=theme.CARD_BG, fg=theme.TEXT_MUTED,
                font=(theme.FONT_FAMILY, 8, "bold"), justify="center",
            ).grid(row=0, column=col, sticky="ew", padx=3)

        rows_container = tk.Frame(inner, bg=theme.CARD_BG)
        rows_container.pack(padx=10)
        popup_state["rows_container"] = rows_container

        for vinculo in recurso["vinculos"]:
            self._renderizar_vinculo_row(popup_state, vinculo)

        linha_adicionar = tk.Frame(inner, bg=theme.CARD_BG)
        linha_adicionar.pack(fill="x", padx=10, pady=(10, 0))

        RoundedButton(
            linha_adicionar, "+  Adicionar vínculo",
            command=lambda: self._adicionar_vinculo(popup_state),
            width=300, height=34, radius=8,
            bg=theme.SURFACE, hover=theme.SURFACE_HOVER,
            fg=theme.TEXT, outline=theme.BORDER,
            font=(theme.FONT_FAMILY, 10, "bold"),
        ).pack(fill="x")

        linha_acoes = tk.Frame(inner, bg=theme.CARD_BG)
        linha_acoes.pack(fill="x", padx=10, pady=10)

        RoundedButton(
            linha_acoes, "Cancelar",
            command=lambda: self._cancelar_configurar_recurso(recurso),
            width=140, height=34, radius=8,
            bg=theme.SURFACE, hover=theme.SURFACE_HOVER,
            fg=theme.TEXT, outline=theme.BORDER,
            font=(theme.FONT_FAMILY, 10, "bold"),
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))

        RoundedButton(
            linha_acoes, "Salvar",
            command=lambda: self._salvar_configurar_recurso(recurso),
            width=140, height=34, radius=8,
            bg=theme.PURPLE, hover=theme.PURPLE_HOVER,
            fg=theme.TEXT,
            font=(theme.FONT_FAMILY, 10, "bold"),
        ).pack(side="left", fill="x", expand=True, padx=(4, 0))

        popup.update_idletasks()
        popup.geometry(f"+{x}+{y}")

        recurso["popup"] = popup
        root = self.winfo_toplevel()
        recurso["popup_click_binding"] = root.bind(
            "<Button-1>", lambda e: self._on_configurar_popup_click(e, recurso), add="+",
        )
        recurso["popup_unmap_binding"] = root.bind(
            "<Unmap>", lambda _e: self._salvar_configurar_recurso(recurso), add="+",
        )

    def _on_configurar_popup_click(self, event, recurso):
        popup = recurso["popup"]
        if popup is None:
            return
        widget = self.winfo_containing(event.x_root, event.y_root)
        node = widget
        while node is not None:
            if node in (popup, recurso["configurar_btn"]):
                return
            node = getattr(node, "master", None)
        self._salvar_configurar_recurso(recurso)

    def _salvar_configurar_recurso(self, recurso):
        """Comita explicitamente o valor atual dos campos de cada vínculo —
        não dá pra confiar só no <FocusOut> (RoundedButton é um Canvas, não
        tira o foco do campo ao ser clicado, então fechar direto sem clicar
        em outro lugar antes nunca disparava o commit)."""
        for vinculo in recurso["vinculos"]:
            if vinculo["tarefa_index"] is not None:
                self._validar_vinculo_tempo(vinculo, "fim")
        self._fechar_configurar_recurso(recurso)

    def _cancelar_configurar_recurso(self, recurso):
        """Descarta tudo que mudou desde que o popup foi aberto — edições,
        vínculos adicionados/removidos, tarefa vinculada trocada."""
        snapshot = recurso.get("_snapshot_vinculos")
        if snapshot is not None:
            recurso["vinculos"] = [dict(v) for v in snapshot]
        self._fechar_configurar_recurso(recurso)

    def _fechar_configurar_recurso(self, recurso):
        recurso.pop("_snapshot_vinculos", None)
        if recurso["popup"] is not None:
            recurso["popup"].destroy()
            recurso["popup"] = None
        root = self.winfo_toplevel()
        if recurso["popup_click_binding"] is not None:
            root.unbind("<Button-1>", recurso["popup_click_binding"])
            recurso["popup_click_binding"] = None
        if recurso["popup_unmap_binding"] is not None:
            root.unbind("<Unmap>", recurso["popup_unmap_binding"])
            recurso["popup_unmap_binding"] = None

    @staticmethod
    def _configure_vinculo_row_columns(row):
        row.grid_columnconfigure(0, weight=0, minsize=120)  # vincular tarefa
        row.grid_columnconfigure(1, weight=0, minsize=52)    # t. inicial tarefa
        row.grid_columnconfigure(2, weight=0, minsize=52)    # t. inicial recurso
        row.grid_columnconfigure(3, weight=0, minsize=52)    # t. final recurso
        row.grid_columnconfigure(4, weight=0, minsize=52)    # t. final tarefa
        row.grid_columnconfigure(5, weight=0, minsize=26)    # lixeira

    def _renderizar_vinculo_row(self, popup_state, vinculo):
        wrapper = tk.Frame(popup_state["rows_container"], bg=theme.CARD_BG)
        wrapper.pack(fill="x", pady=3)

        row = tk.Frame(wrapper, bg=theme.CARD_BG)
        row.pack(fill="x")
        self._configure_vinculo_row_columns(row)

        # se a tarefa vinculada foi apagada nesse meio tempo, trata como se
        # não tivesse vínculo — evita estourar índice fora do range.
        if vinculo["tarefa_index"] is not None and vinculo["tarefa_index"] > len(self.task_rows):
            vinculo["tarefa_index"] = None

        # o erro vermelho não sobrevive a fechar/reabrir o popup — só some
        # sozinho ao editar de novo ENQUANTO a tela tá aberta.
        vinculo["erro_vermelho"] = None

        dropdown = Dropdown(
            row, self._tarefas_disponiveis(), initial=vinculo["tarefa_index"],
            width=120, height=32, parent_bg=theme.CARD_BG,
            placeholder="Selecionar",
            options_provider=self._tarefas_disponiveis,
            command=lambda valor: self._on_vinculo_tarefa_selecionada(popup_state, vinculo, valor),
        )
        dropdown.grid(row=0, column=0, sticky="w", padx=3)

        t_inicial_tarefa = PlaceholderNumericEntry(row, placeholder=0, width=6)
        t_inicial_tarefa.grid(row=0, column=1, sticky="ew", padx=3, ipady=4)
        t_inicial_tarefa.set_locked(True)

        t_inicial_recurso = PlaceholderNumericEntry(row, placeholder=0, width=6)
        t_inicial_recurso.grid(row=0, column=2, sticky="ew", padx=3, ipady=4)

        t_final_recurso = PlaceholderNumericEntry(row, placeholder=0, width=6)
        t_final_recurso.grid(row=0, column=3, sticky="ew", padx=3, ipady=4)

        t_final_tarefa = PlaceholderNumericEntry(row, placeholder=0, width=6)
        t_final_tarefa.grid(row=0, column=4, sticky="ew", padx=3, ipady=4)
        t_final_tarefa.set_locked(True)

        remove_btn = TrashIconButton(row, command=lambda: self._remover_vinculo(popup_state, vinculo), size=18)
        remove_btn.grid(row=0, column=5, sticky="e", padx=3)

        msg_label = tk.Label(
            wrapper, text="", bg=theme.CARD_BG,
            font=(theme.FONT_FAMILY, 8), anchor="w", justify="left",
        )
        # não empacotado aqui — só aparece quando tiver algo a avisar
        # (_mostrar_msg_vinculo/_limpar_msg_vinculo cuidam do pack/pack_forget)

        vinculo["frame"] = wrapper
        vinculo["msg_label"] = msg_label
        vinculo["dropdown"] = dropdown
        vinculo["t_inicial_tarefa_entry"] = t_inicial_tarefa
        vinculo["t_inicial_recurso_entry"] = t_inicial_recurso
        vinculo["t_final_recurso_entry"] = t_final_recurso
        vinculo["t_final_tarefa_entry"] = t_final_tarefa

        if vinculo["tarefa_index"] is not None:
            tp = self.task_rows[vinculo["tarefa_index"] - 1]["entries"][1].get_value()
            t_inicial_tarefa.set_value(0)
            t_final_tarefa.set_value(tp)
            t_inicial_recurso.set_locked(False)
            t_inicial_recurso.set_value(vinculo["t_inicial_recurso"])
            t_final_recurso.set_locked(False)
            t_final_recurso.set_value(vinculo["t_final_recurso"])
            self._renderizar_msg_vinculo(vinculo)
        else:
            t_inicial_recurso.set_locked(True)
            t_final_recurso.set_locked(True)

        t_inicial_recurso.bind(
            "<FocusOut>", lambda _e, v=vinculo: self._validar_vinculo_tempo(v, "inicio"), add="+",
        )
        t_final_recurso.bind(
            "<FocusOut>", lambda _e, v=vinculo: self._validar_vinculo_tempo(v, "fim"), add="+",
        )
        for entry in (t_inicial_recurso, t_final_recurso):
            entry.bind("<Key>", lambda _e, v=vinculo: self._limpar_erro_vermelho_vinculo(v), add="+")

    def _adicionar_vinculo(self, popup_state):
        vinculo = {"tarefa_index": None, "t_inicial_recurso": 0, "t_final_recurso": 0}
        popup_state["recurso"]["vinculos"].append(vinculo)
        self._renderizar_vinculo_row(popup_state, vinculo)

    def _remover_vinculo(self, popup_state, vinculo):
        vinculo["frame"].destroy()
        popup_state["recurso"]["vinculos"].remove(vinculo)

    def _on_vinculo_tarefa_selecionada(self, popup_state, vinculo, indice_tarefa):
        tp = self.task_rows[indice_tarefa - 1]["entries"][1].get_value()

        vinculo["tarefa_index"] = indice_tarefa
        vinculo["t_inicial_recurso"] = 0
        vinculo["t_final_recurso"] = tp
        vinculo["erro_vermelho"] = None

        vinculo["t_inicial_tarefa_entry"].set_value(0)
        vinculo["t_final_tarefa_entry"].set_value(tp)

        vinculo["t_inicial_recurso_entry"].set_locked(False)
        vinculo["t_inicial_recurso_entry"].set_value(0)

        vinculo["t_final_recurso_entry"].set_locked(False)
        vinculo["t_final_recurso_entry"].set_value(tp)

        self._renderizar_msg_vinculo(vinculo)

    def _validar_vinculo_tempo(self, vinculo, campo):
        if vinculo["tarefa_index"] is None:
            return  # nenhuma tarefa vinculada ainda, nada pra validar

        tp = self.task_rows[vinculo["tarefa_index"] - 1]["entries"][1].get_value()
        inicio = vinculo["t_inicial_recurso_entry"].get_value()
        fim = vinculo["t_final_recurso_entry"].get_value()

        # único bloqueio de verdade: início tem que ser MENOR que fim
        # (inválido só se início > fim — empate é permitido). Um vínculo que
        # ultrapassa o tp da tarefa não é travado aqui — a tarefa pode mudar
        # de duração depois, e não queremos truncar nada, só avisar (aviso
        # amarelo, calculado em _renderizar_msg_vinculo).
        if inicio > fim:
            # reverte só o campo que causou o problema, pro padrão natural dele
            if campo == "inicio":
                vinculo["t_inicial_recurso_entry"].set_value(0)
            else:
                vinculo["t_final_recurso_entry"].set_value(tp)
            vinculo["erro_vermelho"] = "Tempo inicial do recurso deve ser menor que o final"
            self._renderizar_msg_vinculo(vinculo)
            return

        vinculo["t_inicial_recurso"] = vinculo["t_inicial_recurso_entry"].get_value()
        vinculo["t_final_recurso"] = vinculo["t_final_recurso_entry"].get_value()
        self._renderizar_msg_vinculo(vinculo)

    def _limpar_erro_vermelho_vinculo(self, vinculo):
        """No <Key>: some com o erro vermelho assim que o usuário começa a
        editar de novo — diferente do aviso amarelo, que é recalculado (some
        só quando a condição em si for corrigida)."""
        if vinculo["erro_vermelho"]:
            vinculo["erro_vermelho"] = None
            self._renderizar_msg_vinculo(vinculo)

    def _renderizar_msg_vinculo(self, vinculo):
        """Decide o que mostrar embaixo da linha do vínculo: erro vermelho
        (bloqueio, tem prioridade) > aviso amarelo (vínculo excede o tp da
        tarefa, não bloqueia) > nada."""
        if vinculo["erro_vermelho"]:
            self._mostrar_msg_vinculo(vinculo, vinculo["erro_vermelho"], theme.DANGER)
            return

        tp = self.task_rows[vinculo["tarefa_index"] - 1]["entries"][1].get_value()
        if vinculo["t_final_recurso"] > tp:
            self._mostrar_msg_vinculo(vinculo, "Vínculo excede tempo da tarefa", "#ffd43b")
        else:
            self._limpar_msg_vinculo(vinculo)

    @staticmethod
    def _mostrar_msg_vinculo(vinculo, mensagem, cor):
        vinculo["msg_label"].config(text=mensagem, fg=cor)
        vinculo["msg_label"].pack(anchor="w", padx=3, pady=(0, 4))

    @staticmethod
    def _limpar_msg_vinculo(vinculo):
        vinculo["msg_label"].config(text="")
        vinculo["msg_label"].pack_forget()
