from matplotlib.patches import Patch

from models.periodo import TipoPeriodo
from views import theme

CHART_EXECUCAO = theme.PURPLE
CHART_TROCA_CONTEXTO = "#f7b955"
CHART_ESPERA = theme.PURPLE_DARK  # mesma borda da execução/troca, só que vazada (sem preenchimento)
CHART_BLOQUEIO = theme.DANGER  # hachurado -- direto e inversão usam a mesma cor, só muda a trama
HACHURA_BLOQUEIO_DIRETO = "///"
HACHURA_BLOQUEIO_INVERSAO = "xxx"


def construir_legenda(ax, fig, tarefas_resultado, cores_recursos, ancora_y):
    """Monta a legenda do gráfico de escalonamento e anexa no eixo — só
    entra o que de fato aparece no resultado dessa rodada (FCFS não ganha
    entrada de bloqueio, por exemplo; troca de contexto só entra se tiver
    largura de verdade, não só o período zero-width que todo despacho gera).
    Fica ancorada na metade direita, com o TOPO em `ancora_y` (fração da
    figura) — cresce pra baixo a partir dali, não pra cima a partir do fundo
    da área reservada. Recursos sempre por último, cada um com a cor real."""
    handles = [Patch(facecolor=CHART_EXECUCAO, edgecolor=theme.PURPLE_DARK, label="Execução")]

    tipos_presentes = {periodo.tipo for tr in tarefas_resultado for periodo in tr.periodos}
    tem_troca_visivel = any(
        periodo.tipo == TipoPeriodo.TROCA_CONTEXTO and periodo.fim > periodo.inicio
        for tr in tarefas_resultado for periodo in tr.periodos
    )

    if tem_troca_visivel:
        handles.append(Patch(facecolor=CHART_TROCA_CONTEXTO, edgecolor=theme.PURPLE_DARK, label="Troca de contexto"))
    if any(tr.esperas for tr in tarefas_resultado):
        handles.append(Patch(facecolor="none", edgecolor=CHART_ESPERA, linewidth=1.2, label="Espera"))
    if TipoPeriodo.BLOQUEIO_DIRETO in tipos_presentes:
        handles.append(Patch(
            facecolor="none", edgecolor=CHART_BLOQUEIO, hatch=HACHURA_BLOQUEIO_DIRETO, label="Bloqueio direto",
        ))
    if TipoPeriodo.BLOQUEIO_INVERSAO in tipos_presentes:
        handles.append(Patch(
            facecolor="none", edgecolor=CHART_BLOQUEIO, hatch=HACHURA_BLOQUEIO_INVERSAO, label="Bloqueio (inversão)",
        ))

    recursos_usados = sorted({
        recurso.id for tr in tarefas_resultado for recurso, _, _ in tr.recursos_em_uso
    })
    for recurso_id in recursos_usados:
        cor = (cores_recursos or {}).get(recurso_id, theme.TEXT_MUTED)
        handles.append(Patch(facecolor=cor, edgecolor=cor, label=f"Recurso {recurso_id}"))

    # "div" de baixo dividida em duas metades: esquerda vazia (por enquanto),
    # direita INTEIRA ocupada pela legenda — em fração da FIGURA (não do
    # eixo, pra posição não entrar num loop de realimentação com o
    # tight_layout). loc="upper left" ancora o TOPO da legenda em ancora_y —
    # ela cresce pra baixo sozinha, do tamanho que precisar.
    legenda = ax.legend(
        handles=handles, loc="upper left", bbox_to_anchor=(0.52, ancora_y, 0.46, 0.001),
        bbox_transform=fig.transFigure,
        mode="expand", ncol=1, fontsize=8, title="Legenda",
        facecolor=theme.CARD_BG, edgecolor=theme.BORDER, labelcolor=theme.TEXT,
    )
    legenda.get_title().set_color(theme.TEXT)
    legenda.get_title().set_fontsize(9)
    legenda.get_frame().set_alpha(0.9)
    return legenda
