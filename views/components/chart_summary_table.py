from views import theme

ALTURA_LINHA = 0.045


def construir_tabela_resumo(fig, resultado, n_trocas, ancora_y):
    """Monta a tabela de resumo (algoritmo, médias, trocas — o que antes
    ficava no título, em cima do gráfico) no canto inferior ESQUERDO, com o
    topo em `ancora_y` (mesma âncora da legenda, do lado oposto). Cria um
    eixo dedicado só pra tabela, em coordenadas da figura, e devolve ele
    (pra poder remover/reposicionar nas passadas de ajuste de layout) junto
    com a altura que ela ocupa."""
    linhas = [
        ("Algoritmo", str(resultado.parametros.algoritmo)),
        ("Tt médio", f"{resultado.medias.tt:.2f} s"),
        ("Tw médio", f"{resultado.medias.tw:.2f} s"),
        ("1ª exec. média", f"{resultado.medias.t1a_exec:.2f} s"),
        ("Trocas de contexto", str(n_trocas)),
    ]
    if resultado.parametros.eficiencia is not None:
        linhas.append(("Eficiência", f"{resultado.parametros.eficiencia:.3f}"))
    altura = len(linhas) * ALTURA_LINHA

    tabela_ax = fig.add_axes((0.02, ancora_y - altura, 0.46, altura))
    tabela_ax.axis("off")
    tabela_ax.set_facecolor(theme.CARD_BG)

    tabela = tabela_ax.table(
        cellText=[[chave, valor] for chave, valor in linhas],
        cellLoc="left", loc="upper left", bbox=(0, 0, 1, 1),
        colWidths=[0.62, 0.38],
    )
    tabela.auto_set_font_size(False)
    tabela.set_fontsize(8)

    for (_row, col), cell in tabela.get_celld().items():
        cell.set_edgecolor(theme.BORDER)
        cell.set_facecolor(theme.CARD_BG)
        texto = cell.get_text()
        texto.set_color(theme.TEXT_MUTED if col == 0 else theme.TEXT)
        if col == 0:
            texto.set_fontweight("bold")

    return tabela_ax, altura
