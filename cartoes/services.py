"""Lógica de negócio de cartão de crédito: em qual fatura cada parcela de
uma compra cai (considerando o dia de fechamento) e pagamento de fatura.
"""

import calendar
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from financas.models import Despesa

from .models import CompraCartao, FaturaCartao, ParcelaCompraCartao

DUAS_CASAS = Decimal('0.01')


class FaturaJaPagaError(Exception):
    """A fatura já foi paga — não dá pra pagar de novo."""


class FaturaVaziaError(Exception):
    """Não tem nenhuma compra lançada nessa fatura."""


def _quantize(valor: Decimal) -> Decimal:
    return valor.quantize(DUAS_CASAS, rounding=ROUND_HALF_UP)


def _somar_meses(ano: int, mes: int, n: int) -> tuple:
    """(ano, mes) depois de somar `n` meses — mesma ideia de
    `financas.services.gerar_despesas_recorrentes_do_mes`."""
    mes_total = (mes - 1) + n
    return ano + mes_total // 12, mes_total % 12 + 1


def _fatura_da_parcela(cartao, data_compra: date, indice_parcela: int) -> tuple:
    """Em que (ano, mês) cai a parcela `indice_parcela` (0-based) de uma
    compra feita em `data_compra`: se a compra foi feita depois do dia de
    fechamento, a 1ª parcela só entra na fatura do mês seguinte."""
    ano, mes = data_compra.year, data_compra.month
    if data_compra.day > cartao.dia_fechamento:
        ano, mes = _somar_meses(ano, mes, 1)
    return _somar_meses(ano, mes, indice_parcela)


def data_vencimento_fatura(cartao, ano: int, mes: int) -> date:
    """Data de vencimento de uma fatura — pode cair no mesmo mês do
    fechamento (vencimento > fechamento) ou no mês seguinte."""
    if cartao.dia_vencimento > cartao.dia_fechamento:
        ano_venc, mes_venc = ano, mes
    else:
        ano_venc, mes_venc = _somar_meses(ano, mes, 1)
    ultimo_dia = calendar.monthrange(ano_venc, mes_venc)[1]
    return date(ano_venc, mes_venc, min(cartao.dia_vencimento, ultimo_dia))


def registrar_compra(cartao, descricao: str, valor_total: Decimal, numero_parcelas: int, data_compra: date) -> CompraCartao:
    """Cria a compra e já gera 1 parcela por mês, cada uma na FaturaCartao
    certa (criada sob demanda). A última parcela absorve a diferença de
    arredondamento, igual a tabela de amortização de empréstimo."""
    compra = CompraCartao.objects.create(
        cartao=cartao, descricao=descricao, valor_total=valor_total,
        numero_parcelas=numero_parcelas, data_compra=data_compra,
    )
    valor_parcela = _quantize(valor_total / numero_parcelas)
    soma = Decimal('0')
    for idx in range(numero_parcelas):
        ano, mes = _fatura_da_parcela(cartao, data_compra, idx)
        fatura, _ = FaturaCartao.objects.get_or_create(cartao=cartao, ano=ano, mes=mes)
        valor = (valor_total - soma) if idx == numero_parcelas - 1 else valor_parcela
        soma += valor
        ParcelaCompraCartao.objects.create(compra=compra, fatura=fatura, numero=idx + 1, valor=valor)
    return compra


def pagar_fatura(fatura: FaturaCartao, data_pagamento: date = None) -> None:
    """Marca a fatura como paga e gera a Despesa correspondente — mesmo
    padrão de `emprestimos.services.registrar_pagamento_parcela`."""
    if fatura.paga:
        raise FaturaJaPagaError
    valor = fatura.valor_total
    if valor <= 0:
        raise FaturaVaziaError

    data_pagamento = data_pagamento or date.today()
    despesa = Despesa.objects.create(
        usuario=fatura.cartao.usuario,
        categoria=fatura.cartao.categoria,
        descricao=f'Fatura {fatura.cartao.nome} — {fatura.mes:02d}/{fatura.ano}',
        valor=valor,
        data=data_pagamento,
    )
    fatura.paga = True
    fatura.data_pagamento = data_pagamento
    fatura.despesa = despesa
    fatura.save(update_fields=['paga', 'data_pagamento', 'despesa'])
