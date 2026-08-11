"""Lógica de negócio de finanças que não depende de API externa.

Geração de despesas recorrentes: como o projeto não tem Celery/cron, a
geração acontece sob demanda — chamada a cada carregamento do dashboard
(mesmo padrão do `PatrimonioSnapshot` em investimentos). É idempotente: usa
`Despesa.recorrente` + ano/mês pra nunca duplicar o lançamento do mês.
"""

import calendar
from datetime import date

from django.utils import timezone

from .models import Despesa, DespesaRecorrente


def gerar_despesas_recorrentes_do_mes(usuario, referencia=None):
    """Garante que toda DespesaRecorrente ativa de `usuario` tenha 1 Despesa
    gerada pro mês de `referencia` (hoje por padrão)."""
    referencia = referencia or timezone.now().date()
    ano, mes = referencia.year, referencia.month
    ultimo_dia = calendar.monthrange(ano, mes)[1]

    for recorrente in DespesaRecorrente.objects.filter(usuario=usuario, ativa=True):
        ja_existe = Despesa.objects.filter(
            recorrente=recorrente, data__year=ano, data__month=mes
        ).exists()
        if not ja_existe:
            dia = min(recorrente.dia_do_mes, ultimo_dia)
            Despesa.objects.create(
                usuario=usuario,
                categoria=recorrente.categoria,
                descricao=recorrente.descricao,
                valor=recorrente.valor,
                data=date(ano, mes, dia),
                recorrente=recorrente,
            )
