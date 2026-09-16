import json
from tkinter import filedialog

from views.screens.build_view.constants import CORRECTION_OPTIONS, SCHEDULER_OPTIONS


def validar_cenario(cenario) -> bool:
    """Confere se um dict lido de um .json é um cenário válido."""
    if not isinstance(cenario, dict):
        return False

    algoritmos_validos = {valor for valor, _ in SCHEDULER_OPTIONS}
    if cenario.get("algoritmo") not in algoritmos_validos:
        return False
    if cenario.get("protocolo_correcao") not in CORRECTION_OPTIONS:
        return False
    if not isinstance(cenario.get("ctx_time"), (int, float)):
        return False
    if not isinstance(cenario.get("quantum"), (int, float)):
        return False

    tarefas = cenario.get("tarefas")
    if not isinstance(tarefas, list):
        return False
    for tarefa in tarefas:
        if not isinstance(tarefa, dict):
            return False
        for chave in ("chegada", "duracao", "prioridade"):
            if not isinstance(tarefa.get(chave), (int, float)):
                return False

    return True


def abrir_cenario_de_arquivo() -> tuple[dict | None, str | None]:
    """Abre o diálogo nativo, lê e valida o arquivo escolhido. Devolve
    (cenário, None) se deu tudo certo, (None, None) se o usuário cancelou o
    diálogo, ou (None, mensagem_de_erro) se o arquivo não presta.

    Usado tanto pelo HomeView (que troca de tela no sucesso) quanto pelo
    BuildView (que já está na tela e só recarrega o formulário) — a lógica
    de abrir/ler/validar é idêntica nos dois, só o que fazer com o resultado
    muda de um pro outro.
    """
    caminho = filedialog.askopenfilename(
        title="Abrir cenário",
        filetypes=[("Cenário (JSON)", "*.json")],
    )
    if not caminho:
        return None, None  # usuário cancelou o diálogo

    try:
        with open(caminho, encoding="utf-8") as arquivo:
            cenario = json.load(arquivo)
    except (OSError, json.JSONDecodeError):
        return None, "Esse arquivo não é um cenário válido."

    if not validar_cenario(cenario):
        return None, "Esse arquivo não é um cenário válido."

    return cenario, None
