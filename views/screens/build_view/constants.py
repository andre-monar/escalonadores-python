ALGO_FCFS = "FCFS"
ALGO_SJF = "SJF"
ALGO_SRTF = "SRTF"
ALGO_ROUND_ROBIN = "RR"
ALGO_PRIOC = "PRIOc"
ALGO_PRIOP = "PRIOp"

SCHEDULER_OPTIONS = [
    (ALGO_FCFS, "FCFS | First-Come, First-Served"),
    (ALGO_ROUND_ROBIN, "RR | Round-Robin"),
    (ALGO_SJF, "SJF | Shortest Job First"),
    (ALGO_SRTF, "SRTF | Shortest Remaining Time First"),
    (ALGO_PRIOC, "PRIOc | Prioridade Cooperativa"),
    (ALGO_PRIOP, "PRIOp | Prioridade Preemptiva"),
]
ALGORITMOS_DESABILITADOS = set()
ALGORITMOS_COM_PRIORIDADE = {ALGO_PRIOC, ALGO_PRIOP}

CORRECTION_OPTIONS = ["Nenhum", "Herança", "Teto"]
CORRECTION_DEFAULT = "Nenhum"

SIDEBAR_WIDTH = 400
SIDEBAR_PAD = 18
