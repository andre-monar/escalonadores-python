import json
from tkinter import filedialog

from views.cenario_io import abrir_cenario_de_arquivo


class CenarioMixin:
    def _build_cenario_dict(self) -> dict:
        """Todos os inputs do formulário, inclusive os campos ocultos/travados
        no momento (quantum, protocolo de correção, prioridade) — só assim dá
        pra trocar de algoritmo depois de recarregar sem perder nada."""
        return {
            "algoritmo": self.scheduler_dropdown.get(),
            "ctx_time": self.ctx_entry.get_value(),
            "quantum": self.quantum_entry.get_value(),
            "protocolo_correcao": self.correction_dropdown.get(),
            "tarefas": [
                {
                    "chegada": row["entries"][0].get_value(),
                    "duracao": row["entries"][1].get_value(),
                    "prioridade": row["entries"][2].get_value(),
                }
                for row in self.task_rows
            ],
        }

    def _on_save_click(self):
        caminho = filedialog.asksaveasfilename(
            title="Salvar cenário",
            defaultextension=".json",
            filetypes=[("Cenário (JSON)", "*.json")],
        )
        if not caminho:
            return  # usuário cancelou o diálogo

        cenario = self._build_cenario_dict()
        with open(caminho, "w", encoding="utf-8") as arquivo:
            json.dump(cenario, arquivo, indent=2, ensure_ascii=False)

    def _on_open_scenario_click(self):
        cenario, erro = abrir_cenario_de_arquivo()
        if erro:
            self._mostrar_erro_tarefas(erro)
            return
        if cenario is None:
            return  # usuário cancelou o diálogo

        self.carregar_cenario(cenario)

    def carregar_cenario(self, cenario: dict):
        """Preenche a tela inteira a partir de um dict já validado (validar_cenario).
        Chame ANTES de mostrar essa tela — a ordem importa: o algoritmo primeiro,
        pra especificações/trava de prioridade já nascerem certas nas tarefas."""
        self.scheduler_dropdown.set_value(cenario["algoritmo"])
        self.ctx_entry.set_value(cenario["ctx_time"])
        self.quantum_entry.set_value(cenario["quantum"])
        self.correction_dropdown.set_value(cenario["protocolo_correcao"])

        for row in list(self.task_rows):
            row["frame"].destroy()
        self.task_rows.clear()

        tarefas = cenario["tarefas"] or [{}, {}]
        for dado in tarefas:
            self._add_task_row()
            chegada_entry, duracao_entry, prioridade_entry = self.task_rows[-1]["entries"]
            chegada_entry.set_value(dado.get("chegada", 0))
            duracao_entry.set_value(dado.get("duracao", 0))
            prioridade_entry.set_value(dado.get("prioridade", 1))

        self._limpar_erro_specs()
        self._limpar_erro_tarefas()
        self._draw_empty_chart()
