import tkinter as tk

from algoritmos.fcfs import fcfs
from algoritmos.prioc import prioc
from algoritmos.priop import priop
from algoritmos.round_robin import round_robin
from algoritmos.sjf import sjf
from algoritmos.srtf import srtf
from views import theme
from views.components.rounded_button import RoundedButton
from views.screens.build_view.tarefas import gerar_tarefas_aleatorias

NUM_CENARIOS = 50
QUANTUM_LOTE = 2
CTX_TIME_LOTE = 0

# nome exibido -> como rodar o algoritmo pra esse lote (RR usa o quantum
# fixo do lote; PRIOp roda sem protocolo, já que os cenários sorteados não
# declaram recurso nenhum — "Nenhum" não faz diferença sem disputa)
ALGORITMOS_DO_LOTE = [
    ("FCFS", lambda tarefas: fcfs(tarefas, ctx_time=CTX_TIME_LOTE)),
    ("RR", lambda tarefas: round_robin(tarefas, ctx_time=CTX_TIME_LOTE, quantum=QUANTUM_LOTE)),
    ("SJF", lambda tarefas: sjf(tarefas, ctx_time=CTX_TIME_LOTE)),
    ("SRTF", lambda tarefas: srtf(tarefas, ctx_time=CTX_TIME_LOTE)),
    ("PRIOc", lambda tarefas: prioc(tarefas, ctx_time=CTX_TIME_LOTE)),
    ("PRIOp", lambda tarefas: priop(tarefas, ctx_time=CTX_TIME_LOTE, protocolo=None)),
]


def _tarefas_validas_sorteadas():
    """Sorteia um cenário (mesmo gerador do botão "Sortear cenário") e
    descarta/renumera igual `_build_tarefas` já faz na tela: linha com
    duração 0 é só de exibição, não entra na simulação."""
    tarefas = []
    proximo_id = 1
    for tarefa in gerar_tarefas_aleatorias():
        if tarefa.tp <= 0:
            continue
        tarefa.id = proximo_id
        tarefas.append(tarefa)
        proximo_id += 1
    return tarefas


def _rodar_lote():
    """R9: sorteia NUM_CENARIOS cenários e roda os seis algoritmos em cada
    um, somando tt/tw/1ª exec. pra depois tirar a média — mesmo formato do
    cenário 4.7 do enunciado. Devolve uma linha por algoritmo."""
    somas = {nome: [0.0, 0.0, 0.0] for nome, _ in ALGORITMOS_DO_LOTE}
    rodados = 0

    for _ in range(NUM_CENARIOS):
        tarefas = _tarefas_validas_sorteadas()
        if not tarefas:
            continue  # sorteio degenerado (todas as 5 vieram com duração 0) — raríssimo, pula
        rodados += 1
        for nome, algoritmo in ALGORITMOS_DO_LOTE:
            resultado = algoritmo(tarefas)
            soma = somas[nome]
            soma[0] += resultado.medias.tt
            soma[1] += resultado.medias.tw
            soma[2] += resultado.medias.t1a_exec

    linhas = []
    for nome, _ in ALGORITMOS_DO_LOTE:
        tt, tw, t1a = somas[nome]
        linhas.append((nome, tt / rodados, tw / rodados, t1a / rodados))
    return linhas


def mostrar_popup_lote(parent):
    """Roda o lote e mostra o resultado num popup, com botão de fechar."""
    linhas = _rodar_lote()

    popup = tk.Toplevel(parent)
    popup.title("Resultado do lote")
    popup.configure(bg=theme.CARD_BG)
    popup.transient(parent.winfo_toplevel())

    tk.Label(
        popup,
        text=(
            f"Médias sobre {NUM_CENARIOS} cenários sorteados "
            f"(quantum={QUANTUM_LOTE} s, custo de troca={CTX_TIME_LOTE} s)"
        ),
        bg=theme.CARD_BG, fg=theme.TEXT, font=(theme.FONT_FAMILY, 11, "bold"),
        justify="left",
    ).pack(padx=20, pady=(18, 12), anchor="w")

    tabela = tk.Frame(popup, bg=theme.CARD_BG)
    tabela.pack(padx=20, pady=(0, 8))

    for col, texto in enumerate(["Algoritmo", "Tt", "Tw", "1ª exec."]):
        tk.Label(
            tabela, text=texto, bg=theme.CARD_BG, fg=theme.TEXT_MUTED,
            font=(theme.FONT_FAMILY, 9, "bold"),
        ).grid(row=0, column=col, padx=12, pady=(0, 6), sticky="w")

    for linha_idx, (nome, tt, tw, t1a) in enumerate(linhas, start=1):
        for col, valor in enumerate([nome, f"{tt:.2f} s", f"{tw:.2f} s", f"{t1a:.2f} s"]):
            tk.Label(
                tabela, text=valor, bg=theme.CARD_BG,
                fg=theme.TEXT if col == 0 else theme.TEXT_MUTED,
                font=(theme.FONT_FAMILY, 10, "bold" if col == 0 else "normal"),
            ).grid(row=linha_idx, column=col, padx=12, pady=3, sticky="w")

    RoundedButton(
        popup, "Fechar",
        command=popup.destroy,
        width=120, height=40, radius=10,
        bg=theme.SURFACE, hover=theme.SURFACE_HOVER,
        fg=theme.TEXT, outline=theme.BORDER,
        font=(theme.FONT_FAMILY, 10, "bold"),
    ).pack(pady=(4, 18))

    popup.update_idletasks()
    raiz = parent.winfo_toplevel()
    popup.geometry(f"+{raiz.winfo_rootx() + 100}+{raiz.winfo_rooty() + 100}")
