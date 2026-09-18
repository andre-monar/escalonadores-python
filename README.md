# Simulador de Escalonamento de Tarefas

Projeto prático da disciplina de **Sistemas Operacionais**, ministrada por **Vinícius da Silva Borges**. Oitavo semestre de Engenharia da Computação na **Faculdade Engenheiro Salvador Arena**.

## Grupo

| Nome | RA |
|------|----|
| André Mendes Garcia | 081230012 |
| Felipe Lira Silva | 081230006 |
| Pedro Henrique Simões Reys | 081230012 |
| Vinicius Yamaguti Augusto | 081220040 |

## Descrição

Simulador de escalonamento de tarefas em um processador único, escrito em Python com interface gráfica (Tkinter). Implementa os seis algoritmos clássicos — FCFS, SJF, SRTF, Round-Robin, prioridade cooperativa e prioridade preemptiva — apresentando para cada um o diagrama de tempo e as métricas por tarefa (tempo de execução, tempo de processamento, tempo de espera e tempo até a primeira execução).

Além dos algoritmos básicos, o simulador trata recursos de uso exclusivo e reproduz o fenômeno da inversão de prioridades sob prioridade preemptiva, com os mecanismos de correção de herança e teto de prioridade. Também implementa envelhecimento de prioridade (eliminando a inanição sob prioridade cooperativa), sorteio de cenários — único ou em lote, para comparar os seis algoritmos — e a gravação/recarregamento de cenários em arquivo.

## Instalação

**[Baixe o aplicativo clicando aqui](https://github.com/andre-monar/escalonadores-python/releases/download/v1.0/Escalonadores.exe)**

[Baixe o cenário de exemplo clicando aqui](https://github.com/andre-monar/escalonadores-python/releases/download/v1.0/cenario_exemplo.json)

## Documentação

- [Tutorial de execução](./docs/tutorial_execucao.pdf) 
- [Tutorial de uso](./docs/tutorial_uso.pdf)
- [Documentação técnica](./docs/documentacao_projeto.pdf) 

## Por onde começar

1. Abra o programa e siga o tutorial de execução.
2. Reproduza um cenário de exemplo pelo tutorial de uso.
3. Consulte a documentação técnica para entender o código.


## Estrutura do repositório

```
escalonadores-python/
|-- main.py                  Ponto de entrada do programa
|-- algoritmos/              Os algoritmos de escalonamento
|-- models/                  Estruturas de dados (Tarefa, Recurso, Periodo, Resultado...)
|-- views/                   Interface gráfica (Tkinter)
|   |-- screens/             Telas do programa (inicial e de montar cenário)
|   `-- components/          Widgets e trechos de UI reutilizáveis
|-- tests/                   Testes unitários dos algoritmos
`-- docs/                    Documentação
```

## Arquivos de código

- `main.py` — abre a janela principal do programa.
- `algoritmos/fcfs.py` — First-Come, First-Served.
- `algoritmos/sjf.py` — Shortest Job First.
- `algoritmos/srtf.py` — Shortest Remaining Time First.
- `algoritmos/round_robin.py` — Round-Robin (com quantum e custo de troca).
- `algoritmos/prioc.py` — Prioridade cooperativa, com envelhecimento de prioridade.
- `algoritmos/priop.py` — Prioridade preemptiva, com recurso de uso exclusivo, inversão de prioridades, herança e teto.
- `algoritmos/validacoes.py` — validações compartilhadas entre algoritmos (ex.: quantum menor que o custo de troca).
- `algoritmos/_montar_resultado.py` — monta o resultado final (métricas por tarefa e médias) a partir dos períodos simulados; usado por todos os algoritmos.
- `algoritmos/_derivar_grafico.py` — deriva os dados usados só pelo desenho do gráfico (esperas, intervalos de uso de recurso) a partir dos períodos.
- `models/tarefa.py` — `Tarefa` e `Recurso` (o vínculo de uma tarefa com um recurso de uso exclusivo).
- `models/periodo.py` — `Periodo` e `TipoPeriodo` (execução, troca de contexto, bloqueio direto/inversão de prioridades).
- `models/resultado.py` — `ResultadoSimulacao`, métricas por tarefa e médias, parâmetros da simulação.
- `views/app.py` — janela principal e troca entre telas.
- `views/theme.py` — cores e fontes usadas na interface.
- `views/cenario_io.py` — salvar/abrir um cenário em arquivo JSON, com validação.
- `views/screens/home_view.py` — tela inicial (criar cenário novo, abrir um existente, rodar lote de cenários).
- `views/screens/build_view/` — tela de montar um cenário e ver o gráfico gerado:
  - `__init__.py` — monta a tela e chama o algoritmo escolhido.
  - `specs.py` — campos de configuração (custo de troca, quantum, protocolo de correção, fator de envelhecimento).
  - `tarefas.py` — cadastro das tarefas e sorteio de cenário aleatório.
  - `recursos.py` — declaração de recursos de uso exclusivo e seus vínculos com as tarefas.
  - `chart.py` — desenha o diagrama de tempo.
  - `cenario.py` — salvar/carregar o cenário atual da tela.
- `views/components/` — peças de interface reutilizáveis (botões, dropdown, etc.), incluindo a legenda do gráfico (`chart_legend.py`), a tabela de resumo (`chart_summary_table.py`) e o comparativo em lote (`batch_table.py`).
- `tests/` — testes unitários dos algoritmos.

## Funcionalidades

| O que faz | Onde |
|-----------|------|
| Os algoritmos de escalonamento | `algoritmos/` |
| Métricas por tarefa e médias (tt, tp, tw, 1ª exec.) | `algoritmos/_montar_resultado.py` |
| Quantum e custo de troca de contexto configuráveis; eficiência | `views/screens/build_view/specs.py`, `algoritmos/round_robin.py` |
| Recurso de uso exclusivo e inversão de prioridades | `views/screens/build_view/recursos.py`, `algoritmos/priop.py` |
| Herança de prioridade | `algoritmos/priop.py` |
| Teto de prioridade | `algoritmos/priop.py` |
| Envelhecimento de prioridade (elimina inanição) | `algoritmos/prioc.py` |
| Sortear um cenário único | `views/screens/build_view/tarefas.py` |
| Rodar lote de cenários e comparar médias entre algoritmos | `views/components/batch_table.py` |
| Salvar e recarregar um cenário | `views/cenario_io.py`, `views/screens/build_view/cenario.py` |