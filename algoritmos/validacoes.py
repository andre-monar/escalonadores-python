class ErroValidacao(ValueError):
    """Parâmetro de simulação inválido — a mensagem é pra aparecer pro usuário, não é bug."""

def validar_quantum(ctx_time: float, quantum: float) -> None:
    if quantum <= ctx_time:
        raise ErroValidacao("O quantum precisa ser maior que o tempo de troca de contexto!")