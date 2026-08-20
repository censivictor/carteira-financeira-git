"""Exception handler customizado da API — hoje só existe pra traduzir a
mensagem de rate limit (DRF manda `Throttled` em inglês por padrão, e o
resto do app é todo em português)."""

from rest_framework.exceptions import Throttled
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None and isinstance(exc, Throttled):
        if exc.wait is not None:
            segundos = int(exc.wait)
            detail = f'Muitas tentativas. Tente de novo em {segundos} segundo{"s" if segundos != 1 else ""}.'
        else:
            detail = 'Muitas tentativas. Tente de novo em instantes.'
        response.data = {'detail': detail}

    return response
